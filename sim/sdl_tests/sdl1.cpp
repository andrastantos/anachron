// To get things going we need:
//     sudo apt install libsdl2-dev libsdl2-image-dev
//#include "sdl_wrapper.h"

#include <iostream>
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <SDL2/SDL_thread.h>
#include <queue>
#include <vector>
#include <array>
#include <algorithm>
#include <atomic>
#include <thread>

extern "C" {
//#include "defs.h"

//#define basename basename
//#include "bfd.h"
//#undef basename

//#include "libiberty.h"
//#include "sim/sim.h"

//#include "sim-main.h"
//#include "sim-base.h"
//#include "sim-options.h"
////#include "sim-io.h"
////#include "sim-signal.h"
////#include "sim-hw.h"
}

#define SIM_ASSERT SDL_assert

class SpinLock {
    std::atomic_flag locked;
    std::thread::id holder;
public:
    void lock() {
        while (locked.test_and_set(std::memory_order_acquire)) // acquire lock
        {
            // Lock is held by someone, let's see if it's us...
            if (holder != std::this_thread::get_id()) break;
            // Since C++20, it is possible to update atomic_flag's
            // value only when there is a chance to acquire the lock.
            // See also: https://stackoverflow.com/questions/62318642
        #if defined(__cpp_lib_atomic_flag_test)
            while (lock.test(std::memory_order_relaxed)); // test lock
        #endif
        }
        holder = std::this_thread::get_id();
    }
    void unlock() {
        locked.clear(std::memory_order_release);
    }
};

class Sentinel {
    SDL_mutex *mutex;
    SpinLock *lock;
public:
    explicit Sentinel(SDL_mutex *mutex): mutex(mutex), lock(nullptr) { SDL_LockMutex(mutex); }
    explicit Sentinel(SpinLock &lock): mutex(nullptr), lock(&lock) { this->lock->lock(); }
    ~Sentinel() {
        if (mutex != nullptr) SDL_UnlockMutex(mutex);
        if (lock != nullptr) lock->unlock();
    }
};

template <size_t N> struct ArraySizeHelper { char _[N]; };
template <typename T, size_t N> ArraySizeHelper<N> makeArraySizeHelper(T(&)[N]);
#define ARRAY_SIZE(a)  sizeof(makeArraySizeHelper(a))


template <typename T, size_t size = sizeof(T) * 8> class ShadowReg {
protected:
    T active_value;
    volatile T next_value;
    SpinLock update_lock;
    bool pending;
    static_assert(size <= sizeof(T)*8, "Size of ShadowReg cannot be larger then the size of its underlying type");
public:
    ShadowReg() {}
    ShadowReg(const T &val): active_value(val), next_value(val), pending(false) {}

    operator T() const { return get(); }
    void set(const T &val) {
        Sentinel sentinel(update_lock);
        next_value = (T)(val & ((1ULL << size) - 1));
        pending = true;
    }
    void set_part(const T &val, size_t start_bit, size_t part_size) {
        T mask = ((1 << part_size) - 1) << start_bit;
        set(get_next() & ~mask | (val << start_bit) & mask);
    }
    T get() const { return active_value; }
    T get_next() const { return next_value; }
    bool is_pending() { return pending; }
    void update() {
        Sentinel sentinel(update_lock);
        if (pending) {
            active_value = next_value;
        }
        pending = false;
    }
};

template <typename Tbase> class ShadowReg<Tbase*, sizeof(ptrdiff_t)*8> {
protected:
    typedef Tbase *T;
    T active_value;
    volatile T next_value;
    SpinLock update_lock;
    bool pending;
public:
    ShadowReg() {}
    ShadowReg(const T &val): active_value(val), next_value(val), pending(false) {}

    operator T() const { return get(); }
    void set(const T &val) {
        Sentinel sentinel(update_lock);
        next_value = val;
        pending = true;
    }
    void set_part(const T &val, size_t start_bit, size_t part_size) {
        T mask = ((1 << part_size) - 1) << start_bit;
        set(get_next() & ~mask | (val << start_bit) & mask);
    }
    T get() const { return active_value; }
    T get_next() const { return next_value; }
    bool is_pending() { return pending; }
    void update() {
        Sentinel sentinel(update_lock);
        if (pending) {
            active_value = next_value;
        }
        pending = false;
    }
};

template <> class ShadowReg<bool> {
protected:
    bool active_value;
    volatile bool next_value;
    SpinLock update_lock;
    bool pending;
public:
    ShadowReg() {}
    ShadowReg(const bool &val): active_value(val), next_value(val), pending(false) {}

    operator bool() const { return get(); }
    void set(const bool &val) {
        Sentinel sentinel(update_lock);
        next_value = val;
        pending = true;
    }
    bool get() const { return active_value; }
    bool get_next() const { return next_value; }
    bool is_pending() { return pending; }
    void update() {
        Sentinel sentinel(update_lock);
        if (pending) {
            active_value = next_value;
        }
        pending = false;
    }
};

template <typename T, size_t size = sizeof(T) * 8> class StatusReg {
protected:
    T value;
public:
    StatusReg() {}
    StatusReg(const T &val): value(val) {}

    operator T() const { return get(); }
    void set(const T &val) {
        value = val & ((1 << size) - 1);
    }
    T get() const {
        return value;
    }
};

class ClearOnWriteReg: public StatusReg<bool> {
public:
    void clear(const bool &val) { if (val) StatusReg<bool>::set(false); }
};


struct Dma
{
    // For sprites we always comsume a full scan-line (implemented through setting row_size to be the right amount).
    // For planes we use post_increment to adjust for differences between screen width and plane pitch.
    // This matches the HW, where sprite data is pre-fetched during horizontal blanking, independent of x offset
    // setting.
public:
    ShadowReg<uint32_t *> memory;
    ShadowReg<uint32_t, 30> base_addr; // measured in DWORDs
    ShadowReg<uint8_t, 5> update_mask; // measured in powers of two. Used for wrap-around addressing
    ShadowReg<int8_t> post_increment; // measured in DWORDs
    StatusReg<uint32_t, 30> cur_addr; // measured in DWORDs
protected:
    uint8_t bits_left;
    uint32_t cur_data; // measured in DWORDs
    uint32_t row_start; // measured in DWORDs
    uint32_t row_size; // measured in DWORDs
public:
    void restart() {
        cur_addr = base_addr.get();
        bits_left = 0;
        row_start = cur_addr;
    }
    void increment_addr(int8_t amount) {
        uint32_t increment_mask = (1ULL << update_mask) - 1;
        uint32_t addr_mask = UINT32_MAX - increment_mask;
        cur_addr = (cur_addr.get() & addr_mask) | ((cur_addr.get() + amount) & increment_mask);
    }
    void next_row() {
        if (row_size == 0) {
            increment_addr(post_increment.get());
        } else {
            increment_addr(row_start + row_size - cur_addr);
        }
        row_start = cur_addr;
        bits_left = 0;
    }
    uint8_t get_bits(uint8_t num_bits) {
        SIM_ASSERT(num_bits == 1 || num_bits == 2 || num_bits == 4 || num_bits == 8);
        if (bits_left < num_bits) {
            SIM_ASSERT(bits_left == 0);
//            printf("0x%08x\n", cur_addr.get());
            cur_data = memory.get()[cur_addr.get()];
            increment_addr(1);
            //cur_addr = cur_addr.get()+1;
            bits_left = 32;
        }
        bits_left -= num_bits;
        uint8_t ret_val = cur_data & ((1 << num_bits) - 1);
        cur_data >>= num_bits;
        return ret_val;
    }
    explicit Dma(void *memory = nullptr):
        memory((uint32_t*)memory),
        base_addr(0),
        post_increment(0),
        cur_addr(0),
        bits_left(0),
        cur_data(0),
        update_mask(0),
        row_start(0),
        row_size(0)
    {}
    void update() {
        memory.update();
        base_addr.update();
        post_increment.update();
        update_mask.update();
    }
    void set_memory(void *memory) { this->memory.set((uint32_t *)memory); }
};

enum BppSettings {
    bpp1 = 0,
    bpp2 = 1,
    bpp4 = 2,
    bpp8 = 3
};

size_t bpp_to_bit_cnt[] = {1,2,4,8};

static const uint16_t sprite_width = 32;
static const uint16_t sprite_height = 32;
static const uint8_t sprite_bpp = 2;
static const size_t plane_cnt = 4;
static const size_t sprite_cnt = 8;

//static int32_t mask(int32_t a, size_t num_bits) {
//    int32_t mask = (1 << num_bits) - 1;
//    int32_t sign_bits = 0xffffffff - mask;
//    a &= mask;
//    if ((a & (1 << (num_bits-1)) != 0) a |= sign_bits;
//    return a;
//}

template <typename T, size_t num_bits> T umask(T a) {
    T mask = (1 << num_bits) - 1;
    return a & mask;
}

class PlaneOrSprite: public Dma
{
public:
    PlaneOrSprite(void *memory = nullptr):
        Dma(memory)
    {}
    // Composition interface
    virtual uint16_t get_start_x(bool is_high_res) const = 0;
    virtual uint16_t get_start_y() const = 0;
    virtual uint16_t get_end_x(bool is_high_res) const = 0;
    virtual uint16_t get_end_y() const = 0;
    virtual BppSettings get_bpp() const = 0;
    virtual bool get_enabled() const = 0;
    virtual uint8_t get_draw_order() const = 0;
    // DMA interface
    virtual uint8_t get_next_pixel() = 0;
    virtual void set_collision() = 0;
};

class PlaneConfig: public PlaneOrSprite
{
public:
    ShadowReg<uint16_t> x;
    ShadowReg<uint16_t> y;
    ShadowReg<BppSettings> bpp;
    ShadowReg<bool> enabled;
    ShadowReg<uint8_t, 4> draw_order;
    ShadowReg<uint8_t> palette_ofs;
    StatusReg<bool> collision;

    PlaneConfig(void *memory = nullptr):
        PlaneOrSprite(memory),
        x(0),
        bpp(bpp1),
        enabled(false),
        draw_order(0),
        palette_ofs(0),
        collision(false)
    {}

    virtual uint16_t get_start_x(bool is_high_res) const override { return is_high_res ? x.get() : x.get() / 2; }
    virtual uint16_t get_start_y() const override { return 0; }
    virtual uint16_t get_end_x(bool is_high_res) const override { return 0xffff; }
    virtual uint16_t get_end_y() const override { return 0xffff; }
    virtual BppSettings get_bpp() const override { return bpp; }
    virtual bool get_enabled() const override { return enabled; }
    virtual uint8_t get_draw_order() const override { return draw_order; }

    virtual uint8_t get_next_pixel() override { uint8_t raw_pixel = get_bits(bpp_to_bit_cnt[bpp]); return raw_pixel ? raw_pixel + palette_ofs : 0; }

    void clear_collision() { collision = false; }
    virtual void set_collision() override { collision = true; }

    void update() {
        x.update();
        bpp.update();
        enabled.update();
        draw_order.update();
        palette_ofs.update();
        Dma::update();
    }
};

class SpriteConfig: public PlaneOrSprite
{
public:
    ShadowReg<uint16_t> x;
    ShadowReg<uint16_t> start_y;
    ShadowReg<uint16_t> end_y;
    ShadowReg<bool> enabled;
    ShadowReg<uint8_t, 4> draw_order;
    ShadowReg<uint8_t> palette1;
    ShadowReg<uint8_t> palette2;
    ShadowReg<uint8_t> palette3;
    StatusReg<bool> collision;

public:
    explicit SpriteConfig(void *memory = nullptr):
        PlaneOrSprite(memory),
        x(0),
        start_y(0),
        end_y(0),
        enabled(false),
        draw_order(0),
        collision(false)
    {
        Dma::update_mask.set(31);
        Dma::update_mask.update();
        row_size = sprite_width * sprite_bpp / 32;
    }
    virtual uint16_t get_start_x(bool is_high_res) const override { return is_high_res ? x.get() : x.get() / 2; }
    virtual uint16_t get_start_y() const override { return start_y; }
    virtual uint16_t get_end_x(bool is_high_res) const override { return get_start_x(is_high_res) + sprite_width; }
    virtual uint16_t get_end_y() const override { return end_y; }
    virtual BppSettings get_bpp() const override { return bpp2; }
    virtual bool get_enabled() const override { return enabled; }
    virtual uint8_t get_draw_order() const override { return draw_order; }

    virtual uint8_t get_next_pixel() {
        uint8_t bits =  get_bits(sprite_bpp);
        switch (bits) {
            case 0: return 0;
            case 1: return palette1;
            case 2: return palette2;
            case 3: return palette3;
            default: SIM_ASSERT(false); return 0;
        }
    }

    void clear_collision() { collision = false; }
    virtual void set_collision() override { collision = true; }

    void update() {
        x.update();
        start_y.update();
        end_y.update();
        enabled.update();
        draw_order.update();
        palette1.update();
        palette2.update();
        palette3.update();
        Dma::update();
    }
};

// According to http://tinyvga.com/vga-timing, the following timing are to be obeyed:
//
// Mode                Back Porch     Sync Pulse     Front Porch        Active Area         Total      Setup
//   640x480@60Hz  H     48             96             16                 640                 800        160
//     25.175HMz   V     33              2             10                 480                 525         45
//   640x400@70Hz  H     48             96             16                 640                 800        160
//     25.175HMz   V     35              2             12                 400                 449         49
//   768x576@60Hz  H    104             80             24                 768                 976        208
//     34.96MHz    V     17              3              1                 576                 597         21
//  1024x768@60Hz  H    160            136             24                1024                1344        320
//     65MHz       V     29              6              3                 768                 806         38
//
// Converting these to our resolutions give us the following timings:
//
// Mode                Back Porch     Sync Pulse     Front Porch        Active Area         Total      Setup     Pixel replication
//
//   640x480@60Hz  H     24             48              8                 320                 400         80        0.5
//     12.5875MHz  V     33              2             10                 480                 525         45          1
//   320x240@60Hz  H     24             48              8                 320                 400         80          1
//     12.5875MHz  V     33              2             10                 480                 525         45          2
//   Timing regs   H     11             35             39                                     199
//                 V    512            514                                479                 524

//   640x400@60Hz  H     24             48              8                 320                 400         80        0.5
//     12.5875MHz  V     35              2             12                 400                 449         49          1
//   320x200@60Hz  H     24             48              8                 320                 400         80          1
//     12.5875MHz  V     35              2             12                 400                 449         49          2
//   Timing regs   H     11             35             39                                     199
//                 V    434            436                                399                 448
//
// (based on 768x576@60Hz, not exact):
//   512x384@60Hz  H     36             26              8                 256                 326         70        0.5
//     11.6773MHz  V     17              3              1                 576                 597         21        1.5 ????
//   256x192@60Hz  H     36             26              8                 256                 326         70          1
//     11.6773MHz  V     17              3              1                 576                 597         21          3
//   Timing regs   H     17             30             34                                     162
//                 V    592            595                                575                 596
//
// (based on 1024x768@60Hz):
//   512x384@60Hz  H     40             34              6                 256                 336         80          0.5
//     16.25MHz    V     29              6              3                 768                 806         38          2
//   256x192@60Hz  H     40             34              6                 256                 336         80          1
//     16.25MHz    V     29              6              3                 768                 806         38          4
//   Timing regs   H     19             36             39                                     167
//                 V    796            802                                767                 805
//
// Horizontal pixel counting starts at the back-porch, vertical at the start of the active area. So for VGA for
// instance, the top-left corner is coordinates 160;0.
// This system makes both X and Y offsets unsigned, but requires SW to adjust the base address for sprites
// that are to be at negative Y coordinates.
//
// Horizontal smooth scrolling is a bit annoying in high-res: X offset must be measured in half pixels.
// So, the X offset LSB is 'special' and need to be masked to 0 for low-res modes.
//
// Horizontal timing is set up in double-clock quantities. This allows all parameters to fit within 8-bit quantities.
// Vertical timing unfortunately has to be exact due to all the odd numbers in the timing table. Still, most values,
// except for vertical total fits in way less than 8 bits.
//
// Unfortunately scan-line doubling is not transparent (because total number of scan-lines never seem to be
// divisible by the repetition count). So the vertical timing will have to programmed for the full vertical
// resolution and a repetition-count register should be set up appropriately.
// Nevertheless, for sprites the Y coordinate is counted in 'virtual' scan-lines, that is in the actual
// resolution of the screen.
//
// Pixel compositing starts immediately at the back-porch, but bits are not pulled for planes and sprites
// for which the X coordinate is greater than the current position. For the non-visible regions of the
// scan-lines, the composited pixel is replaced by the appropriate (sync/blanking) level at the last moment,
// before the DACs.

template <size_t bit_idx> uint32_t bool_to_bit(bool value) { return value ? (1 << bit_idx) : 0; }
template <size_t bit_idx> bool get_bit(uint32_t value) { return (value >> bit_idx) & 1 != 0; }

class VideoCore
{
public:
    // We have two resolutions per resolution (ha!) supported. Low-res, which generates one pixel
    // per clock cycle and high-res, which generates two clocks per clock cycle (one on each edge).
    //
    // Thus for
    // To get from video_clock to pixel_clock, we need a pre-divider.
    // This pre-divider is
    // For low-res, we generate one pixel per pixel_clock, for high-res, we generate two (one on each edge).
    // For all timing modes, the resulting timing values are divisible by 2, so the we further divide
    // horizontal timing values by 2. In other words, horizontal timing is measured in two-pixel intervals
    // in low-res mode and 4-pixel intervals in high-res mode.
    //
    // The start coordinate for a plane or sprite is in pixels (low- or high-res).
    //
    // horizontal timing is measured in double-pixel-clock quantities.
    // We have a contiguous horizontal counter with trigger points for the various events.
    ShadowReg<uint8_t, 8> h_total;
    ShadowReg<uint8_t, 6> h_back_porch_end;
    ShadowReg<uint8_t, 6> h_sync_end;
    ShadowReg<uint8_t, 6> h_front_porch_end;
    ShadowReg<bool>       h_high_res;
    // Vertical
    ShadowReg<uint16_t, 10> v_total;
    ShadowReg<uint16_t, 10> v_active_end;
    ShadowReg<uint16_t, 10> v_back_porch_end;
    ShadowReg<uint16_t, 10> v_sync_end;
    ShadowReg<uint8_t,   2> v_replication; // set to 0 for no replication, 1 for double scan-line, etc.
    // Global
    ShadowReg<bool> enabled;
    ShadowReg<bool> global_int_en;
    ShadowReg<bool> line_int_en;
    ShadowReg<bool> read_int_en;
    ShadowReg<bool> vertical_int_en;
    ShadowReg<uint8_t, plane_cnt> plane_collision_int_en;
    ShadowReg<uint8_t, sprite_cnt> sprite_collision_int_en;
    ShadowReg<uint16_t, 10> line_int_val;
    // Status
    ClearOnWriteReg global_int;
    ClearOnWriteReg line_int;
    ClearOnWriteReg read_int;
    ClearOnWriteReg vertical_int;
    std::array<ClearOnWriteReg, plane_cnt> plane_collisions;
    std::array<ClearOnWriteReg, sprite_cnt> sprite_collisions;
    // Palette handling
    uint8_t palette_idx;
    std::vector<SDL_Color> palette256;
    std::vector<SDL_Color>  palette16;
    // profiling
    size_t frame_cnt;
    size_t run_time;
protected:
    template<typename _InputIterator> uint32_t combine_collisions(_InputIterator begin, _InputIterator end) const {
        uint32_t ret_val = 0;
        for (size_t bit_idx=0; begin != end; ++begin, bit_idx) {
            ret_val |= begin->get() ? 1 << bit_idx : 0;
        }
        return ret_val;
    }
    template<typename _InputIterator> void clear_collisions(_InputIterator begin, _InputIterator end, uint32_t mask) {
        for (size_t bit_idx=0; begin != end; ++begin, bit_idx) {
            if ((mask >> bit_idx) & 1 != 0) {
                begin->clear(true);
            }
        }
    }


protected:
    std::vector<uint8_t> frame_buffer;
    SDL_Surface *surface;
    SDL_Texture *texture;
    SDL_Renderer *renderer;
    SDL_Window *window;

    size_t screen_size() { return get_screen_w() * get_screen_h(); }

    std::array<PlaneConfig, plane_cnt> planes;
    std::array<SpriteConfig, sprite_cnt> sprites;

    mutable uint32_t read_shadow;

public:
    VideoCore(void *memory = nullptr):
        h_total(0),
        h_back_porch_end(0),
        h_sync_end(0),
        h_front_porch_end(0),
        h_high_res(0),
        v_total(0),
        v_active_end(0),
        v_back_porch_end(0),
        v_sync_end(0),
        v_replication(0),
        enabled(false),
        surface(nullptr),
        texture(nullptr),
        renderer(nullptr),
        window(nullptr),
        palette256(256),
        palette16(32),
        frame_cnt(0),
        run_time(0)
    {
        set_memory(memory);
        for (auto &entry: palette16)  { entry.r = 0; entry.g = 0; entry.b = 0; entry.a = 255; }
        for (auto &entry: palette256) { entry.r = 0; entry.g = 0; entry.b = 0; entry.a = 255; }
    }

    ~VideoCore() {
        if (surface != nullptr) SDL_FreeSurface(surface);
        if (texture != nullptr) SDL_DestroyTexture(texture);
    }

    void set_memory(void *new_memory) {
        for (auto &plane: planes) plane.set_memory(new_memory);
        for (auto &sprite: sprites) sprite.set_memory(new_memory);
    }

    size_t get_screen_w() const { return (h_total-h_front_porch_end) * (h_high_res ? 4 : 2); }
    size_t get_screen_h() const { return (v_active_end + 1) / (v_replication + 1); }

    void set_renderer(SDL_Renderer *renderer) { this->renderer = renderer; }
    void set_window(SDL_Window *window) { this->window = window; }

    // Compose all planes and sprites into a single (still indexed) target
    struct ElementBounds { size_t start_x, end_x, start_y, end_y; };
    void compose() {
        // Create a composition order
        std::vector<PlaneOrSprite *> compose_order(planes.size() + sprites.size());
        for (auto &pos: compose_order) pos = nullptr;
        for (auto &plane: planes) {
            if (plane.get_enabled()) {
                compose_order[plane.get_draw_order()] = &plane;
            }
        }
        for (auto &sprite: sprites) {
            if (sprite.get_enabled()) {
                compose_order[sprite.get_draw_order()] = &sprite;
            }
        }
        // Compact the composition array
        size_t new_size = std::remove_if(compose_order.begin(), compose_order.end(), [](void *p){return p==nullptr;}) - compose_order.begin();
        compose_order.resize(new_size);

        size_t h = get_screen_h();
        size_t max_x = (h_total+1)*(h_high_res ? 4 : 2)-1;
        size_t h_active_start = (h_front_porch_end+1)*(h_high_res ? 4 : 2)-1;

        // Start with background index
        fill(frame_buffer.begin(), frame_buffer.end(), 0);

        // Render each pixel in composition order
        // Loops are re-ordered for better performance (and less HW accuracy)
        // There's a *ton* that can be optimized here, but I'm not going to spend time on it right away.
        // It's plenty fast even in -O0 and close to 400fps in -O2.
        if (enabled) {
            for (auto &element: compose_order) {
                element->restart();
                ElementBounds element_bounds = {
                    element->get_start_x(h_high_res)        , element->get_end_x(h_high_res),
                    element->get_start_y()                  , element->get_end_y()
                };
                uint8_t *target_pixel = &frame_buffer[0];
                for (size_t y=0;y<h;++y) {
                    for (size_t x=0;x<=max_x;++x) {
                        if (
                            x >= element_bounds.start_x && x < element_bounds.end_x &&
                            y >= element_bounds.start_y && y < element_bounds.end_y
                        ) {
                            uint8_t pixel_idx = element->get_next_pixel();
                            if (pixel_idx != 0 && x > h_active_start) {
                                if (*target_pixel != 0) element->set_collision();
                                *target_pixel = pixel_idx;
                            }
                        }
                        if (x > h_active_start) ++target_pixel;
                    }
                    if (
                        y >= element_bounds.start_y && y < element_bounds.end_y
                    ) {
                        element->next_row();
                    }
                }
            }
        }
    }

    void render() {
        update();
        compose();
        // Determine which palette to use
        BppSettings max_bpp;
        max_bpp = std::max_element(planes.cbegin(), planes.cend(), [](const PlaneConfig &a, const PlaneConfig &b) { return a.bpp.get() < b.bpp.get(); })->bpp.get();
        std::vector<SDL_Color> &palette_to_use = max_bpp > bpp4 ? palette256 : palette16;
        // Convert frame_buffer to RGB pixels and copy to surface as we go
        SDL_LockSurface(surface);
        SDL_Color *target_pixel = (SDL_Color*)(surface->pixels);
        size_t palette_offset = 0;
        size_t odd_offset = max_bpp > bpp4 ? 0 : 16;
        for (auto &source_pixel: frame_buffer) {
            *target_pixel = palette_to_use[source_pixel + palette_offset];
            palette_offset = odd_offset - palette_offset; // For 4-bit modes or less, odd pixels use the upper 16 palette entries, while even ones use the lower 16 ones.
            ++target_pixel;
        }
        SDL_UnlockSurface(surface);
        if (renderer != nullptr) {
            void *tex_pixels;
            int tex_pitch;
            SDL_LockTexture(texture, NULL, &tex_pixels, &tex_pitch);
            SDL_LockSurface(surface);
            SIM_ASSERT(tex_pitch == surface->pitch);
            memcpy(tex_pixels, surface->pixels, surface->h*tex_pitch);
            SDL_UnlockSurface(surface);
            SDL_UnlockTexture(texture);

            SDL_RenderClear(renderer);
            SDL_RenderCopy(renderer, texture, NULL, NULL);
            SDL_RenderPresent(renderer);
        }
        ++frame_cnt;
    }

    void update() {
        size_t old_w = get_screen_w();
        size_t old_h = get_screen_h();
        h_total.update();
        h_back_porch_end.update();
        h_sync_end.update();
        h_front_porch_end.update();
        h_high_res.update();
        v_total.update();
        v_active_end.update();
        v_back_porch_end.update();
        v_sync_end.update();
        v_replication.update();
        enabled.update();
        for (auto &plane: planes) plane.update();
        for (auto &sprite: sprites) sprite.update();

        // Might be a no-op if size didn't actually change.
        if (enabled) {
            frame_buffer.resize(screen_size(), 0);
            size_t new_w = get_screen_w();
            size_t new_h = get_screen_h();
            if (renderer != nullptr) {
                if (old_w != new_w || old_h != new_h || surface == nullptr || texture == nullptr) {
                    if (surface != nullptr) SDL_FreeSurface(surface);
                    surface = SDL_CreateRGBSurfaceWithFormat(0, new_w, new_h, 0, SDL_PIXELFORMAT_ABGR8888);
                    SIM_ASSERT(surface != nullptr);
                    if (texture != nullptr) SDL_DestroyTexture(texture);
                    texture = SDL_CreateTexture(renderer, surface->format->format, SDL_TEXTUREACCESS_STREAMING, surface->w, surface->h);
                    SIM_ASSERT(texture != nullptr);
                    // resize the window. For resolutions below 512 pixels, we make the window size double the resolution, for others, we don't
                    if (window != nullptr) {
                        int double_h = new_w < 512 ? 2 : 1;
                        int double_w = new_h < 384 ? 2 : 1;
                        SDL_SetWindowSize(window, new_w * double_w, new_h * double_h);
                    }
                }
            }
        }
    }
    enum class global_regs {
        h_total                 = 0x000,
        h_back_porch_end        = 0x001,
        h_sync_end              = 0x002,
        h_front_porch_end       = 0x003,
        v_total_high            = 0x004,
        v_active_end_high       = 0x005,
        v_back_porch_end_high   = 0x006,
        v_sync_end_high         = 0x007,
        v_timing_low            = 0x008,
        line_int_val            = 0x009,
                                         // 7           6           5           4           3           2           1           0
        timing_misc             = 0x00a, // ENABLED                 <<<< LINE_INT_LOW >>>>  <<<< V_REPLICATION >>>>             H_HIGH_RES
        int_en                  = 0x010, // G_INT_EN                                                    LINE_INT_EN RD_INT_EN   V_INT_EN
        int_status              = 0x011, // G_INT                                                       LINE_INT    RD_INT      V_INT
        plane_collision_int_en  = 0x012, //                                                 PLN_3       PLN_2       PLN_1       PLN_0
        plane_collision         = 0x013, //                                                 PLN_3       PLN_2       PLN_1       PLN_0
        sprite_collision_int_en = 0x014, // SPRT_7      SPRT_6      SPRT_5      SPRT_4      SPRT_3      SPRT_2      SPRT_1      SPRT_0
        sprite_collision        = 0x015, // SPRT_7      SPRT_6      SPRT_5      SPRT_4      SPRT_3      SPRT_2      SPRT_1      SPRT_0

        palette_idx             = 0x040, // Only indices between 0 and 31 and accepted
        palette_r               = 0x041, // HW might implement only the top 4-5 bits. In simulation (for now at least) we do all 8.
        palette_g               = 0x042, // HW might implement only the top 4-5 bits. In simulation (for now at least) we do all 8.
        palette_b               = 0x043, // HW might implement only the top 4-5 bits. In simulation (for now at least) we do all 8.

        plane_0                 = 0x080,
        plane_1                 = 0x0a0,
        plane_2                 = 0x0c0,
        plane_3                 = 0x0e0,
        sprite_0                = 0x100,
        sprite_1                = 0x120,
        sprite_2                = 0x140,
        sprite_3                = 0x160,
        sprite_4                = 0x180,
        sprite_5                = 0x1a0,
        sprite_6                = 0x1c0,
        sprite_7                = 0x1e0,
    };
    enum class plane_or_sprite_regs {
        base_addr_0              = 0x00,
        base_addr_1              = 0x01,
        base_addr_2              = 0x02,
        base_addr_3              = 0x03, // 7           6           5           4           3           2           1           0
        draw_order__enabled__bpp = 0x04, // ENABLED     BPP[1]      BPP[0]                  ORDER[3]    ORDER[2]    ORDER[1]    ORDER[0]
        post_increment           = 0x05,
        x_0                      = 0x06,
        x_1                      = 0x07,
        y_0                      = 0x08,
        y_1                      = 0x09,
        palette_1                = 0x0a,
    };
    enum class plane_regs {
        update_mask              = 0x0b,
        cur_addr_0               = 0x0c, // Reading this should capture full 32-bit into some shadow register (which is NOT per plane!!!)
        cur_addr_1               = 0x0d,
        cur_addr_2               = 0x0e,
        cur_addr_3               = 0x0f
    };
    enum class sprite_regs {
        palette_2                = 0x0b,
        palette_3                = 0x0c,
        reserved                 = 0x0d,
        end_y_0                  = 0x0e,
        end_y_1                  = 0x0f,
    };

    uint8_t register_read(size_t offset) const {
        switch (offset) {
            case (size_t)global_regs::h_total:                return h_total.get_next();
            case (size_t)global_regs::h_back_porch_end:       return h_back_porch_end.get_next();
            case (size_t)global_regs::h_sync_end:             return h_sync_end.get_next();
            case (size_t)global_regs::h_front_porch_end:      return h_front_porch_end.get_next();
            case (size_t)global_regs::v_total_high:           return v_total.get_next() >> 2;
            case (size_t)global_regs::v_active_end_high:      return v_active_end.get_next() >> 2;
            case (size_t)global_regs::v_back_porch_end_high:  return v_back_porch_end.get_next() >> 2;
            case (size_t)global_regs::v_sync_end_high:        return v_sync_end.get_next() >> 2;
            case (size_t)global_regs::v_timing_low:           return (v_total.get_next() & 3) << 0 |
                                                                     (v_active_end.get_next() & 3) << 2 |
                                                                     (v_back_porch_end.get_next() & 3) << 4 |
                                                                     (v_sync_end.get_next() & 3) << 6;
            case (size_t)global_regs::line_int_val:           return line_int_val.get_next() >> 2;
            case (size_t)global_regs::timing_misc:            return (h_high_res.get_next() & 3) << 0 |
                                                                     (v_replication.get_next() & 3) << 2 |
                                                                     (line_int_val.get_next() & 3) << 4 |
                                                                     bool_to_bit<7>(enabled.get_next());
            case (size_t)global_regs::int_en:                 return bool_to_bit<7>(global_int_en.get_next()) | bool_to_bit<2>(line_int_en.get_next()) | bool_to_bit<1>(read_int_en.get_next()) | bool_to_bit<0>(vertical_int_en.get_next());
            case (size_t)global_regs::int_status:             return bool_to_bit<7>(global_int)               | bool_to_bit<2>(line_int)               | bool_to_bit<1>(read_int)               | bool_to_bit<0>(vertical_int);
            case (size_t)global_regs::plane_collision_int_en: return plane_collision_int_en.get_next();
            case (size_t)global_regs::plane_collision:        return combine_collisions(plane_collisions.cbegin(), plane_collisions.cend());
            case (size_t)global_regs::sprite_collision_int_en:return sprite_collision_int_en.get_next();
            case (size_t)global_regs::sprite_collision:       return combine_collisions(sprite_collisions.cbegin(), sprite_collisions.cend());

            case (size_t)global_regs::palette_idx:            return palette_idx;
            case (size_t)global_regs::palette_r:              return palette16[palette_idx].r;
            case (size_t)global_regs::palette_g:              return palette16[palette_idx].g;
            case (size_t)global_regs::palette_b:              return palette16[palette_idx].b;

            default:
                switch (offset & ~0x1f) {
                    case (size_t)global_regs::plane_0:
                    case (size_t)global_regs::plane_1:
                    case (size_t)global_regs::plane_2:
                    case (size_t)global_regs::plane_3:
                    {
                        size_t plane_idx = (offset - (size_t)global_regs::plane_0) >> 5;
                        const PlaneConfig &plane = planes[plane_idx];
                        switch (offset & 0x1f) {
                            case (size_t)plane_or_sprite_regs::base_addr_0:               return (plane.base_addr.get_next() << 2 >>  0) & 0xff;
                            case (size_t)plane_or_sprite_regs::base_addr_1:               return (plane.base_addr.get_next() << 2 >>  8) & 0xff;
                            case (size_t)plane_or_sprite_regs::base_addr_2:               return (plane.base_addr.get_next() << 2 >> 16) & 0xff;
                            case (size_t)plane_or_sprite_regs::base_addr_3:               return (plane.base_addr.get_next() << 2 >> 24) & 0xff;
                                                                                          //  0x03, // 7           6           5           4           3           2           1           0
                                                                                          //  0x04, // ENABLED     BPP[1]      BPP[0]                  ORDER[3]    ORDER[2]    ORDER[1]    ORDER[0]
                            case (size_t)plane_or_sprite_regs::draw_order__enabled__bpp:  return plane.draw_order.get_next() << 0 |
                                                                                       plane.bpp.get_next() << 5 |
                                                                                       bool_to_bit<7>(plane.enabled.get_next());
                            case (size_t)plane_or_sprite_regs::post_increment:            return plane.post_increment.get_next();
                            case (size_t)plane_or_sprite_regs::x_0:                       return (plane.x.get_next() >> 0) & 0xff;
                            case (size_t)plane_or_sprite_regs::x_1:                       return (plane.x.get_next() >> 8) & 0xff;
                            case (size_t)plane_or_sprite_regs::y_0:                       return (plane.y.get_next() >> 0) & 0xff;
                            case (size_t)plane_or_sprite_regs::y_1:                       return (plane.y.get_next() >> 8) & 0xff;
                            case (size_t)plane_or_sprite_regs::palette_1:               return plane.palette_ofs.get_next();

                            case (size_t)plane_regs::update_mask:               return plane.update_mask.get_next();
                            case (size_t)plane_regs::cur_addr_0:                read_shadow = plane.cur_addr.get();
                                                                                return (read_shadow << 2 >>  0) & 0xff;
                            case (size_t)plane_regs::cur_addr_1:                return (read_shadow << 2 >>  8) & 0xff;
                            case (size_t)plane_regs::cur_addr_2:                return (read_shadow << 2 >> 16) & 0xff;
                            case (size_t)plane_regs::cur_addr_3:                return (read_shadow << 2 >> 24) & 0xff;
                            default:
                                SIM_ASSERT(false);
                        }
                    }
                    case (size_t)global_regs::sprite_0:
                    case (size_t)global_regs::sprite_1:
                    case (size_t)global_regs::sprite_2:
                    case (size_t)global_regs::sprite_3:
                    case (size_t)global_regs::sprite_4:
                    case (size_t)global_regs::sprite_5:
                    case (size_t)global_regs::sprite_6:
                    case (size_t)global_regs::sprite_7:
                    {
                        size_t sprite_idx = (offset - (size_t)global_regs::sprite_0) >> 5;
                        const SpriteConfig &sprite = sprites[sprite_idx];
                        switch (offset & 0x1f) {
                            case (size_t)plane_or_sprite_regs::base_addr_0:              return (sprite.base_addr.get_next() << 2 >>  0) & 0xff;
                            case (size_t)plane_or_sprite_regs::base_addr_1:              return (sprite.base_addr.get_next() << 2 >>  8) & 0xff;
                            case (size_t)plane_or_sprite_regs::base_addr_2:              return (sprite.base_addr.get_next() << 2 >> 16) & 0xff;
                            case (size_t)plane_or_sprite_regs::base_addr_3:              return (sprite.base_addr.get_next() << 2 >> 24) & 0xff;
                                                // 7           6           5           4           3           2           1           0
                                                // ENABLED                                                     ORDER[2]    ORDER[1]    ORDER[0]
                            case (size_t)plane_or_sprite_regs::draw_order__enabled__bpp:      return sprite.draw_order.get_next() << 0 |
                                                                                              bool_to_bit<7>(sprite.enabled.get_next());
                            case (size_t)plane_or_sprite_regs::post_increment:            return sprite.post_increment.get_next();
                            case (size_t)plane_or_sprite_regs::x_0:             return (sprite.x.get_next() >> 0) & 0xff;
                            case (size_t)plane_or_sprite_regs::x_1:             return (sprite.x.get_next() >> 8) & 0xff;
                            case (size_t)plane_or_sprite_regs::y_0:             return (sprite.start_y.get_next() >> 0) & 0xff;
                            case (size_t)plane_or_sprite_regs::y_1:             return (sprite.start_y.get_next() >> 8) & 0xff;

                            case (size_t)plane_or_sprite_regs::palette_1:       return sprite.palette1.get_next();
                            case (size_t)sprite_regs::palette_2:                return sprite.palette2.get_next();
                            case (size_t)sprite_regs::palette_3:                return sprite.palette3.get_next();
                            case (size_t)sprite_regs::end_y_0:                  return (sprite.end_y.get_next() >> 0) & 0xff;
                            case (size_t)sprite_regs::end_y_1:                  return (sprite.end_y.get_next() >> 8) & 0xff;
                            default:
                                SIM_ASSERT(false);
                        }
                    }
                    default:
                        SIM_ASSERT(false);
                } // inner switch
        } // outer switch
        SIM_ASSERT(false);
        return 0;
    }
    void register_write(size_t offset, uint8_t value) {
        switch (offset) {
            case (size_t)global_regs::h_total:                   h_total.set(value); break;
            case (size_t)global_regs::h_back_porch_end:          h_back_porch_end.set(value); break;
            case (size_t)global_regs::h_sync_end:                h_sync_end.set(value); break;
            case (size_t)global_regs::h_front_porch_end:         h_front_porch_end.set(value); break;
            case (size_t)global_regs::v_total_high:              v_total.set_part(value, 2, 8); break;
            case (size_t)global_regs::v_active_end_high:         v_active_end.set_part(value, 2, 8); break;
            case (size_t)global_regs::v_back_porch_end_high:     v_back_porch_end.set_part(value, 2, 8); break;
            case (size_t)global_regs::v_sync_end_high:           v_sync_end.set_part(value, 2, 8); break;
            case (size_t)global_regs::v_timing_low:              v_total.set_part((value >> 0) & 3, 0, 2);
                                                                 v_active_end.set_part((value >> 2) & 3, 0, 2);
                                                                 v_back_porch_end.set_part((value >> 4) & 3, 0, 2);
                                                                 v_sync_end.set_part((value >> 6) & 3, 0, 2);
                                                                 break;
            case (size_t)global_regs::line_int_val:              line_int_val.set_part(value, 2, 8);
            case (size_t)global_regs::timing_misc:               h_high_res.set(get_bit<0>(value));
                                                                 v_replication.set_part((value >> 2) & 3, 0, 2);
                                                                 line_int_val.set_part((value >> 4) & 3, 0, 2);
                                                                 enabled.set(get_bit<7>(value));
                                                                 break;
            case (size_t)global_regs::int_en:                    global_int_en.set(get_bit<7>(value));
                                                                 line_int_en.set(get_bit<2>(value));
                                                                 read_int_en.set(get_bit<1>(value));
                                                                 vertical_int_en.set(get_bit<0>(value));
                                                                 break;
            case (size_t)global_regs::int_status:                global_int.clear(get_bit<7>(value));
                                                                 line_int.clear(get_bit<2>(value));
                                                                 read_int.clear(get_bit<1>(value));
                                                                 vertical_int.clear(get_bit<0>(value));
                                                                 break;
            case (size_t)global_regs::plane_collision_int_en:    plane_collision_int_en.set(value); break;
            case (size_t)global_regs::plane_collision:           clear_collisions(plane_collisions.begin(), plane_collisions.end(), value); break;
            case (size_t)global_regs::sprite_collision_int_en:   sprite_collision_int_en.set(value); break;
            case (size_t)global_regs::sprite_collision:          clear_collisions(sprite_collisions.begin(), sprite_collisions.end(), value); break;

            // There might be a single-frame worth of strange color artifacts if the palette is updated during screen-time. This would be less visible in HW as interpolation happens real-time.
            case (size_t)global_regs::palette_idx:               palette_idx = value & 31; break;
            case (size_t)global_regs::palette_r:                 palette16[palette_idx].r = value; update_palette(); break;
            case (size_t)global_regs::palette_g:                 palette16[palette_idx].g = value; update_palette(); break;
            case (size_t)global_regs::palette_b:                 palette16[palette_idx].b = value; update_palette(); break;

            default:
                switch (offset & ~0x1f) {
                    case (size_t)global_regs::plane_0:
                    case (size_t)global_regs::plane_1:
                    case (size_t)global_regs::plane_2:
                    case (size_t)global_regs::plane_3:
                    {
                        size_t plane_idx = (offset - (size_t)global_regs::plane_0) >> 5;
                        PlaneConfig &plane = planes[plane_idx];
                        switch (offset & 0x1f) {
                            case (size_t)plane_or_sprite_regs::base_addr_0:               plane.base_addr.set_part(value >> 2,  0, 6); break;
                            case (size_t)plane_or_sprite_regs::base_addr_1:               plane.base_addr.set_part(value >> 0,  6, 8); break;
                            case (size_t)plane_or_sprite_regs::base_addr_2:               plane.base_addr.set_part(value >> 0, 14, 8); break;
                            case (size_t)plane_or_sprite_regs::base_addr_3:               plane.base_addr.set_part(value >> 0, 22, 8); break;
                                                                                //  0x03, // 7           6           5           4           3           2           1           0
                                                                                //  0x04, // ENABLED     BPP[1]      BPP[0]                  ORDER[3]    ORDER[2]    ORDER[1]    ORDER[0]
                            case (size_t)plane_or_sprite_regs::draw_order__enabled__bpp:  plane.draw_order.set(value >> 0);
                                                                                plane.bpp.set(BppSettings((value >> 5) & 3));
                                                                                plane.enabled.set(get_bit<7>(value));
                                                                                break;
                            case (size_t)plane_or_sprite_regs::post_increment:            plane.post_increment.set(value); break;
                            case (size_t)plane_or_sprite_regs::x_0:                       plane.x.set_part(value, 0, 8); break;
                            case (size_t)plane_or_sprite_regs::x_1:                       plane.x.set_part(value, 8, 8); break;
                            case (size_t)plane_or_sprite_regs::y_0:                       plane.y.set_part(value, 0, 8); break;
                            case (size_t)plane_or_sprite_regs::y_1:                       plane.y.set_part(value, 8, 8); break;
                            case (size_t)plane_or_sprite_regs::palette_1:               plane.palette_ofs.set(value); break;
                            case (size_t)plane_regs::update_mask:               plane.update_mask.set(value); break;
                            default:
                                SIM_ASSERT(false);
                        }
                        break;
                    }
                    case (size_t)global_regs::sprite_0:
                    case (size_t)global_regs::sprite_1:
                    case (size_t)global_regs::sprite_2:
                    case (size_t)global_regs::sprite_3:
                    case (size_t)global_regs::sprite_4:
                    case (size_t)global_regs::sprite_5:
                    case (size_t)global_regs::sprite_6:
                    case (size_t)global_regs::sprite_7:
                    {
                        size_t sprite_idx = (offset - (size_t)global_regs::sprite_0) >> 5;
                        SpriteConfig &sprite = sprites[sprite_idx];
                        switch (offset & 0x1f) {
                            case (size_t)plane_or_sprite_regs::base_addr_0:              sprite.base_addr.set_part(value >> 2,  0, 6); break;
                            case (size_t)plane_or_sprite_regs::base_addr_1:              sprite.base_addr.set_part(value >> 0,  6, 8); break;
                            case (size_t)plane_or_sprite_regs::base_addr_2:              sprite.base_addr.set_part(value >> 0, 14, 8); break;
                            case (size_t)plane_or_sprite_regs::base_addr_3:              sprite.base_addr.set_part(value >> 0, 22, 8); break;
                                                // 7           6           5           4           3           2           1           0
                                                // ENABLED                                                     ORDER[2]    ORDER[1]    ORDER[0]
                            case (size_t)plane_or_sprite_regs::draw_order__enabled__bpp:      sprite.draw_order.set(value >> 0);
                                                                                              sprite.enabled.set(get_bit<7>(value));
                                                                                              break;
                            case (size_t)plane_or_sprite_regs::x_0:                      sprite.x.set_part(value, 0, 8); break;
                            case (size_t)plane_or_sprite_regs::x_1:                      sprite.x.set_part(value, 8, 8); break;
                            case (size_t)plane_or_sprite_regs::y_0:                sprite.start_y.set_part(value, 0, 8); break;
                            case (size_t)plane_or_sprite_regs::y_1:                sprite.start_y.set_part(value, 8, 8); break;
                            case (size_t)plane_or_sprite_regs::post_increment:     sprite.post_increment.set(value); break;
                            case (size_t)plane_or_sprite_regs::palette_1:          sprite.palette1.set(value); break;
                            case (size_t)sprite_regs::palette_2:                sprite.palette2.set(value); break;
                            case (size_t)sprite_regs::palette_3:                sprite.palette3.set(value); break;
                            case (size_t)sprite_regs::end_y_0:                  sprite.end_y.set_part(value, 0, 8); break;
                            case (size_t)sprite_regs::end_y_1:                  sprite.end_y.set_part(value, 8, 8); break;
                            default:
                                SIM_ASSERT(false);
                        }
                        break;
                    }
                    default:
                        SIM_ASSERT(false);
                } // inner switch
        } // outer switch
    }


    void update_palette() {
        // This is the linear interpolation between two colors for 16 steps idea.
        // It allows for 16 independent ranges of 16 colors each, but the interpolation is not a nice power of two
        // as we have to create 14 interpolated colors (step 16 should reach the target)
        //size_t start_idx = palette_idx >> 1 << 1;
        //uint8_t full_start_idx = start_idx * 8;
        //for (size_t i=0;i<=15;++i) {
        //    palette256[full_start_idx+i].r = (palette16[start_idx].r * (15-i) + palette16[start_idx+1].r * i)/15;
        //    palette256[full_start_idx+i].g = (palette16[start_idx].g * (15-i) + palette16[start_idx+1].g * i)/15;
        //    palette256[full_start_idx+i].b = (palette16[start_idx].b * (15-i) + palette16[start_idx+1].b * i)/15;
        //    palette256[full_start_idx+i].a = 255;
        //}


        // This is the linear interpolation between all 32 palette entries, 8 steps each.
        // Here we require all ranges to be meaningful (i.e. the end of one range is the beginning of another)
        // but the interpolation is a nice power of two: we interpolate 8 steps and reach the target on the 9th step.
        // This also wraps around, that is palette entries 249...255 are interpolated between 248 and 0.
        for (int start_idx = palette_idx - 1; start_idx <= palette_idx; ++start_idx) {
            if (start_idx < 0) continue;
            uint8_t full_start_idx = start_idx * 8;
            for (size_t i=0;i<=7;++i) {
                palette256[full_start_idx+i].r = (palette16[start_idx].r * (8-i) + palette16[(start_idx+1) & 31].r * i)/8;
                palette256[full_start_idx+i].g = (palette16[start_idx].g * (8-i) + palette16[(start_idx+1) & 31].g * i)/8;
                palette256[full_start_idx+i].b = (palette16[start_idx].b * (8-i) + palette16[(start_idx+1) & 31].b * i)/8;
                palette256[full_start_idx+i].a = 255;
            }
        }
    }
};














const size_t default_display_width = 640;
const size_t default_display_height = 480;

static bool initialized = false;

volatile static bool terminate_thread = false;

SDL_mutex *render_mutex = nullptr;
SDL_mutex *big_render_mutex = nullptr; // Only need to take this one if screen resolution changes
SDL_mutex *kbd_mutex = nullptr;

struct KbdEvent {
    SDL_Keysym event;
    bool down_not_up;
};

std::queue<KbdEvent> kbd_queue;

static std::unique_ptr<std::thread> render_thread;

static SDL_Window *main_window = nullptr;
static SDL_Renderer *renderer = nullptr;
static std::unique_ptr<VideoCore> video_core;

static bool display_enabled = false;

void sdl_thread(void *context) {
    VideoCore *video_core = (VideoCore *)context;

    video_core->run_time = SDL_GetTicks();
    while (!terminate_thread) {
        // We'll have to decide how to deal with the keyboard. The code below generates
        // individual events for keypresses (and releases) as a USB (or PS/2) keyboard would.
        //
        // An alternative would be to call SDL_PumpEvents and SDL_GetKeyboardState/SDL_GetModState
        // to get the whole 'scan matrix'.
        //
        // Drain all messages
        //
        // We copy into a local queue first, then put the gathered messages into the kbd_queue.
        // This way we only have to grab kbd_mutex only once
        std::queue<KbdEvent> local_queue;
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) {
                //terminate = true;
            }
            if (e.type == SDL_KEYDOWN || e.type == SDL_KEYUP) {
                KbdEvent event;
                event.event = e.key.keysym;
                event.down_not_up = e.key.type == SDL_KEYDOWN;
                local_queue.push(event);
            }
        }
        if (local_queue.size() > 0) {
            Sentinel sentinel(kbd_mutex);
            while (local_queue.size() > 0) {
                kbd_queue.push(local_queue.front());
                local_queue.pop();
            }
        }

        video_core->render();
    }
    video_core->run_time = SDL_GetTicks() - video_core->run_time;
}


void sdl_wrapper_terminate();


bool sdl_wrapper_init() {
    // Guard for multiple initialization.
    if (initialized) return true;

    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS) < 0) {
        std::cout << "Error SDL2 Initialization : " << SDL_GetError();
        return false;
    }

    if (IMG_Init(IMG_INIT_PNG) == 0) {
        SDL_Quit();
        std::cout << "Error SDL2_image Initialization";
        return false;
    }

    // From here on sdl_wrapper_terminate does the right thing, so even if things go wrong
    // further down, we should consider the framework initialized.
    initialized = true;

    main_window = SDL_CreateWindow(
        "Anachron screen",
        SDL_WINDOWPOS_CENTERED,
        SDL_WINDOWPOS_CENTERED,
        default_display_width,
        default_display_height,
        SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE
    );
    if (main_window == nullptr) goto err_return;

    video_core = std::make_unique<VideoCore>();

    video_core->set_window(main_window);

    renderer = SDL_CreateRenderer(main_window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (renderer == nullptr) goto err_return;

    video_core->set_renderer(renderer);

    render_thread = std::make_unique<std::thread>(sdl_thread, video_core.get());

    return true;

err_return:
    sdl_wrapper_terminate();
    return false;
}

void sdl_wrapper_terminate()
{
    // guard for multiple termination
    if (!initialized) return;

    if (render_thread != nullptr) {
        terminate_thread = true;
        if (render_thread->joinable()) {
            render_thread->join();
        }
    }
    std::cout << "Rendered " << video_core->frame_cnt << " frames in " << video_core->run_time << "ms - " << double(video_core->frame_cnt) / double(video_core->run_time) * 1000.0 << "fps" << std::endl;

    render_thread.reset();

    video_core.reset();

    if (renderer != nullptr) SDL_DestroyRenderer(renderer);
    renderer = nullptr;
    if (main_window != nullptr) SDL_DestroyWindow(main_window);
    main_window = nullptr;

    IMG_Quit();
    SDL_Quit();
    initialized = false;

}

bool sdl_wrapper_kb_has_char()
{
    Sentinel sentinel(kbd_mutex);
    return kbd_queue.size() > 0;
}

bool sdl_wrapper_kb_get_char(uint32_t *key, bool *down_not_up, uint32_t *modifiers) {
    SIM_ASSERT(key != nullptr);
    SIM_ASSERT(down_not_up != nullptr);
    SIM_ASSERT(modifiers != nullptr);
    KbdEvent event;
    {
        Sentinel sentinel(kbd_mutex);
        if (kbd_queue.size() == 0) return false;
        event = kbd_queue.front();
        kbd_queue.pop();
    }
    *down_not_up = event.down_not_up;
    *key = event.event.sym;
    *modifiers = event.event.mod;
    return true;
}





/////////////////////////////////////////////////////////////////////////////////////////////////////
//
// Client code
//
/////////////////////////////////////////////////////////////////////////////////////////////////////




void set_pixel_bpp1(uint8_t *memory, uint32_t offset, size_t pitch, int x, int y, uint8_t color)
{
    offset += y * pitch + x / 8;
    uint8_t mask = 0x1 << (x&7);
    color = (color & 0x01) * 0xff;
    memory[offset] = memory[offset] & ~mask | (color & mask);
}

void set_pixel_bpp2(uint8_t *memory, uint32_t offset, size_t pitch, int x, int y, uint8_t color)
{
    offset += y * pitch + x / 4;
    uint8_t mask = 0x3 << (2*(x&3));
    color = (color & 0x03) * 0x55;
    memory[offset] = memory[offset] & ~mask | (color & mask);
}

void set_pixel_bpp4(uint8_t *memory, uint32_t offset, size_t pitch, int x, int y, uint8_t color)
{
    offset += y * pitch + x / 2;
    uint8_t mask = 0xf << (4*(x&1));
    color = (color & 0x0f) * 0x11;
    memory[offset] = memory[offset] & ~mask | (color & mask);
}

void set_pixel_bpp8(uint8_t *memory, uint32_t offset, size_t pitch, int x, int y, uint8_t color)
{
    offset += y * pitch + x;
    memory[offset] = color;
}

class FrameBuf {
protected:
    uint8_t *memory;
    uint32_t base_addr;
    size_t w;
    size_t h;
    size_t pitch;
    BppSettings bpp;
public:
    FrameBuf(
        uint8_t *memory,
        uint32_t base_addr,
        size_t w,
        size_t h,
        size_t pitch,
        BppSettings bpp
    ) :
        memory(memory),
        base_addr(base_addr),
        w(w),
        h(h),
        pitch(pitch),
        bpp(bpp)
    {}

    FrameBuf(
        uint8_t *memory,
        uint32_t base_addr,
        size_t w,
        size_t h,
        BppSettings bpp
    ) :
        memory(memory),
        base_addr(base_addr),
        w(w),
        h(h),
        pitch(w * bpp_to_bit_cnt[bpp] / 8),
        bpp(bpp)
    {}

    void set_pixel(int x, int y, uint8_t color)
    {
        if (x < 0 || x >= w) return;
        if (y < 0 || y >= h) return;
        switch (bpp) {
            case BppSettings::bpp1: set_pixel_bpp1(memory, base_addr, pitch, x, y, color); break;
            case BppSettings::bpp2: set_pixel_bpp2(memory, base_addr, pitch, x, y, color); break;
            case BppSettings::bpp4: set_pixel_bpp4(memory, base_addr, pitch, x, y, color); break;
            case BppSettings::bpp8: set_pixel_bpp8(memory, base_addr, pitch, x, y, color); break;
            default: SIM_ASSERT(false);
        }
    }

    void draw_rect(int x, int y, int w, int h, uint8_t color)
    {
        for(size_t xx=x;xx<x+w;++xx) {
            set_pixel(xx,y,color);
            set_pixel(xx,y+h-1,color);
        }
        for(size_t yy=y;yy<y+h;++yy) {
            set_pixel(x,yy,color);
            set_pixel(x+w-1,yy,color);
        }
    }

    void fill_rect(int x, int y, int w, int h, uint8_t color) {
        for(size_t xx=x;xx<x+w;++xx) {
            for(size_t yy=y;yy<y+h;++yy) {
                set_pixel(xx,yy,color);
            }
        }
    }

    void clear(uint8_t color = 0) {
        switch (bpp) {
            case BppSettings::bpp1: color = (color & 0x01) * 0xff; break;
            case BppSettings::bpp2: color = (color & 0x03) * 0x55; break;
            case BppSettings::bpp4: color = (color & 0x0f) * 0x11; break;
            case BppSettings::bpp8: color = (color & 0xff) * 0x01; break;
            default: SIM_ASSERT(false);
        }
        memset(memory + base_addr, color, pitch*h);
    }
};

class PlaneOrSpriteBuf: public FrameBuf {
protected:
    VideoCore &core;
    size_t reg_base;
    int16_t y;
public:
    PlaneOrSpriteBuf(
        VideoCore &core,
        size_t reg_base,
        uint8_t *memory,
        uint32_t base_addr,
        size_t w,
        size_t h,
        size_t pitch,
        BppSettings bpp
    ) : FrameBuf(
        memory,
        base_addr,
        w,
        h,
        pitch,
        bpp),
        core(core),
        reg_base(reg_base),
        y(0)
    {
        set_base_addr(base_addr);
    }

    PlaneOrSpriteBuf(
        VideoCore &core,
        size_t reg_base,
        uint8_t *memory,
        uint32_t base_addr,
        size_t w,
        size_t h,
        BppSettings bpp
    ) : FrameBuf(
        memory,
        base_addr,
        w,
        h,
        bpp),
        core(core),
        reg_base(reg_base),
        y(0)
    {
        set_base_addr_reg(base_addr);
        set_palette_1(0);
    }

    void set_base_addr(uint32_t base_addr) {
        this->base_addr = base_addr;
        // Bizarrely we'll have to update the 'y' location to get the base_address written into the registers.
        // This is because of the way negative 'y' coordinates are handled, namely that we patch up the base
        // address
        set_y(get_y());
    }
    uint32_t get_base_addr() {
        return base_addr;
    }
    void set_enabled(bool enabled) {
        uint8_t val = core.register_read(reg_base + (size_t)VideoCore::plane_or_sprite_regs::draw_order__enabled__bpp);
        val = enabled ? val | 0x80 : val & ~0x80;
        core.register_write(
            reg_base + (size_t)VideoCore::plane_or_sprite_regs::draw_order__enabled__bpp,
            val
        );
    }
    bool get_enabled() {
        uint8_t val = core.register_read(reg_base + (size_t)VideoCore::plane_or_sprite_regs::draw_order__enabled__bpp);
        return (val >> 7) & 1;
    }
    void set_draw_order(size_t draw_order) {
        uint8_t val = core.register_read(reg_base + (size_t)VideoCore::plane_or_sprite_regs::draw_order__enabled__bpp);
        val = (val & 0xf0) | (draw_order & 0x0f);
        video_core->register_write(
            reg_base + (size_t)VideoCore::plane_or_sprite_regs::draw_order__enabled__bpp,
            val
        );
    }
    size_t get_draw_order() {
        uint8_t val = core.register_read(reg_base + (size_t)VideoCore::plane_or_sprite_regs::draw_order__enabled__bpp);
        return val & 0xf;
    }

    virtual void set_x(int16_t x) = 0;

    int16_t get_x() const {
        uint16_t screen_start = (video_core->register_read((size_t)VideoCore::global_regs::h_front_porch_end) + 1) * 4;
        uint16_t real_x =
            (video_core->register_read(reg_base + (size_t)VideoCore::plane_or_sprite_regs::x_0) << 0) |
            (video_core->register_read(reg_base + (size_t)VideoCore::plane_or_sprite_regs::x_1) << 8);
        int16_t x = real_x - screen_start;
        if (!is_high_res()) x /= 2;
        return x;
    }

    void set_palette_1(uint8_t palette_ofs) {
        video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::palette_1, palette_ofs);
    }
    uint8_t get_palette_1() const {
        return video_core->register_read(reg_base + (size_t)VideoCore::plane_or_sprite_regs::palette_1);
    }


    virtual void set_y(int16_t y) = 0;
    int16_t get_y() const { return y; }
protected:
    bool is_high_res() const {
        return video_core->register_read((size_t)VideoCore::global_regs::timing_misc) & 1;
    }
    void set_base_addr_reg(uint32_t base_addr) {
        core.register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::base_addr_0, (base_addr >>  0) & 0xff);
        core.register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::base_addr_1, (base_addr >>  8) & 0xff);
        core.register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::base_addr_2, (base_addr >> 16) & 0xff);
        core.register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::base_addr_3, (base_addr >> 24) & 0xff);
    }
};


class PlaneBuf: public PlaneOrSpriteBuf {
public:
    PlaneBuf(
        VideoCore &core,
        size_t plane_idx,
        uint8_t *memory,
        uint32_t base_addr,
        size_t w,
        size_t h,
        size_t pitch,
        BppSettings bpp
    ) : PlaneOrSpriteBuf(
        core,
        calc_reg_base(plane_idx),
        memory,
        base_addr,
        w,
        h,
        pitch,
        bpp)
    {
        set_bpp(bpp);
        set_x(0);
    }

    PlaneBuf(
        VideoCore &core,
        size_t plane_idx,
        uint8_t *memory,
        uint32_t base_addr,
        size_t w,
        size_t h,
        BppSettings bpp
    ) : PlaneOrSpriteBuf(
        core,
        calc_reg_base(plane_idx),
        memory,
        base_addr,
        w,
        h,
        bpp)
    {
        set_bpp(bpp);
        set_update_mask(31);
        set_x(0);
    }

    void set_bpp(BppSettings bpp) {
        uint8_t val = core.register_read(reg_base + (size_t)VideoCore::plane_or_sprite_regs::draw_order__enabled__bpp);
        val = (val & ~(3 << 5)) | (size_t(bpp) << 5);
        video_core->register_write(
            reg_base + (size_t)VideoCore::plane_or_sprite_regs::draw_order__enabled__bpp,
            val
        );
    }
    BppSettings get_bpp() {
        uint8_t val = core.register_read(reg_base + (size_t)VideoCore::plane_or_sprite_regs::draw_order__enabled__bpp);
        return (BppSettings)((val >> 5) & 0x3);
    }

    void set_update_mask(uint8_t update_mask) {
        video_core->register_write(reg_base + (size_t)VideoCore::plane_regs::update_mask, update_mask);
    }
    virtual void set_x(int16_t x) override {
        uint16_t screen_start = (video_core->register_read((size_t)VideoCore::global_regs::h_front_porch_end) + 1) * 4;
        uint16_t real_x = x * (is_high_res() ? 1 : 2) + screen_start;

        video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::x_0, (real_x >> 0) & 0xff);
        video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::x_1, (real_x >> 8) & 0xff);
        // We have to make sure that the next scan-line starts in memory where it should, in case we don't read as much
        // data as a full scan-line is worth
        uint16_t screen_end = (video_core->register_read((size_t)VideoCore::global_regs::h_total) + 1) * 4;
        uint16_t pixels_per_scan_line = (screen_end-screen_start) / (is_high_res() ? 1 : 2);
        size_t pixels_per_plane_line = pixels_per_scan_line-x;
        size_t dwords_per_plane_line = (pixels_per_plane_line * bpp_to_bit_cnt[bpp] + 31) / 32;
        int post_increment = pitch / 4 - dwords_per_plane_line;
        video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::post_increment, post_increment);
    }

    virtual void set_y(int16_t y) override {
        this->y = y;
        if (y < 0) {
            // We need to update the base address such that it hides the missing rows. Each row is 32 pixels long and
            // 2bpp, so 8 bytes in total
            size_t base_offset = -y * pitch;
            set_base_addr_reg(base_addr - base_offset);
        }
        set_base_addr_reg(base_addr);
        video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::y_0, (y >> 0) & 0xff);
        video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::y_1, (y >> 8) & 0xff);
    }

protected:
    static size_t calc_reg_base(size_t plane_idx) {
        return ((size_t)VideoCore::global_regs::plane_1 - (size_t)VideoCore::global_regs::plane_0) * plane_idx + (size_t)VideoCore::global_regs::plane_0;
    }
};


class SpriteBuf: public PlaneOrSpriteBuf {
public:
    SpriteBuf(
        VideoCore &core,
        size_t sprite_idx,
        uint8_t *memory,
        uint32_t base_addr,
        size_t h,
        size_t pitch
    ) : PlaneOrSpriteBuf(
        core,
        calc_reg_base(sprite_idx),
        memory,
        base_addr,
        32,
        h,
        pitch,
        BppSettings::bpp2)
    {}

    SpriteBuf(
        VideoCore &core,
        size_t sprite_idx,
        uint8_t *memory,
        uint32_t base_addr,
        size_t h
    ) : PlaneOrSpriteBuf(
        core,
        calc_reg_base(sprite_idx),
        memory,
        base_addr,
        32,
        h,
        BppSettings::bpp2)
    {
        set_palette_1(0);
        set_palette_2(1);
        set_palette_3(2);
        set_y(0);
        set_x(0);
    }

    void set_palette_2(uint8_t palette_idx) {
        video_core->register_write(reg_base + (size_t)VideoCore::sprite_regs::palette_2, palette_idx);
    }
    uint8_t get_palette_2() const {
        return video_core->register_read(reg_base + (size_t)VideoCore::sprite_regs::palette_2);
    }
    void set_palette_3(uint8_t palette_idx) {
        video_core->register_write(reg_base + (size_t)VideoCore::sprite_regs::palette_3, palette_idx);
    }
    uint8_t get_palette_3() const {
        return video_core->register_read(reg_base + (size_t)VideoCore::sprite_regs::palette_3);
    }
    virtual void set_x(int16_t x) override {
        uint16_t screen_start = (video_core->register_read((size_t)VideoCore::global_regs::h_front_porch_end) + 1) * 4;
        uint16_t real_x = x * (is_high_res() ? 1 : 2) + screen_start;

        video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::x_0, (real_x >> 0) & 0xff);
        video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::x_1, (real_x >> 8) & 0xff);
    }

    virtual void set_y(int16_t y) override {
        this->y = y;
        if (y+h < 0) {
            // We need to position the sprite off-screen. We will just assume the low bits are set to all 1's, so we can avoid an extra register
            // read and some bit-manipulation
            uint16_t v_total =
                video_core->register_read(reg_base + (size_t)VideoCore::global_regs::v_total_high) << 2 + 4;
            video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::y_0, (v_total >> 0) & 0xff);
            video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::y_1, (v_total >> 8) & 0xff);
            video_core->register_write(reg_base + (size_t)VideoCore::sprite_regs::end_y_0, (v_total >> 0) & 0xff);
            video_core->register_write(reg_base + (size_t)VideoCore::sprite_regs::end_y_1, (v_total >> 8) & 0xff);
            return;
        }
        if (y < 0) {
            // We need to update the base address such that it hides the missing rows.
            set_base_addr_reg(base_addr - y * pitch);
            video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::y_0, (0 >> 0) & 0xff);
            video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::y_1, (0 >> 8) & 0xff);
        } else {
            set_base_addr_reg(base_addr);
            video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::y_0, (y >> 0) & 0xff);
            video_core->register_write(reg_base + (size_t)VideoCore::plane_or_sprite_regs::y_1, (y >> 8) & 0xff);
        }
        video_core->register_write(reg_base + (size_t)VideoCore::sprite_regs::end_y_0, ((y+h) >> 0) & 0xff);
        video_core->register_write(reg_base + (size_t)VideoCore::sprite_regs::end_y_1, ((y+h) >> 8) & 0xff);
    }
protected:
    static size_t calc_reg_base(size_t plane_idx) {
        return ((size_t)VideoCore::global_regs::sprite_1 - (size_t)VideoCore::global_regs::sprite_0) * plane_idx + (size_t)VideoCore::global_regs::sprite_0;
    }
};

int main(int argc, char* argv[]) {
    size_t mem_size = 1024*1024;
    uint8_t *memory = (uint8_t*)malloc(mem_size);
    memset(memory, 0, mem_size);
    sdl_wrapper_init();

    video_core->set_memory(memory);

    // Set 320x240 mode
// Mode                Back Porch     Sync Pulse     Front Porch        Active Area         Total      Setup     Pixel replication
//
//   640x480@60Hz  H     24             48              8                 320                 400         80        0.5
//     12.5875MHz  V     33              2             10                 480                 525         45          1
//   320x240@60Hz  H     24             48              8                 320                 400         80          1
//     12.5875MHz  V     33              2             10                 480                 525         45          2
//   Timing regs   H     11             35             39                                     199
//                 V    512            514                                479                 524

    video_core->register_write((size_t)VideoCore::global_regs::h_total                 , 199);
    video_core->register_write((size_t)VideoCore::global_regs::h_back_porch_end        , 11);
    video_core->register_write((size_t)VideoCore::global_regs::h_sync_end              , 35);
    video_core->register_write((size_t)VideoCore::global_regs::h_front_porch_end       , 39);
    video_core->register_write((size_t)VideoCore::global_regs::v_total_high            , 524 >> 2);
    video_core->register_write((size_t)VideoCore::global_regs::v_active_end_high       , 479 >> 2);
    video_core->register_write((size_t)VideoCore::global_regs::v_back_porch_end_high   , 512 >> 2);
    video_core->register_write((size_t)VideoCore::global_regs::v_sync_end_high         , 514 >> 2);
    video_core->register_write((size_t)VideoCore::global_regs::v_timing_low            , ((524 & 3) << 0) | ((479 & 3) << 2) | ((512 & 3) << 4) | ((514 & 3) << 6));
    video_core->register_write((size_t)VideoCore::global_regs::line_int_val            , 0);
                                                                                                // 7           6           5           4           3           2           1           0
                                                                                                // ENABLED                 <<<< LINE_INT_LOW >>>>  <<<< V_REPLICATION >>>>             H_HIGH_RES
    video_core->register_write((size_t)VideoCore::global_regs::timing_misc             , 0x80 | ((0 & 3) << 4) | (1 << 2) | 0x00);
    video_core->register_write((size_t)VideoCore::global_regs::int_en                  , 0);    // G_INT_EN                                                    LINE_INT_EN RD_INT_EN   V_INT_EN
    video_core->register_write((size_t)VideoCore::global_regs::plane_collision_int_en  , 0);    //                                                 PLN_3       PLN_2       PLN_1       PLN_0
    video_core->register_write((size_t)VideoCore::global_regs::sprite_collision_int_en , 0);    // SPRT_7      SPRT_6      SPRT_5      SPRT_4      SPRT_3      SPRT_2      SPRT_1      SPRT_0

    // Setting up plane 0
    std::array<PlaneBuf, 4> planes = {
        PlaneBuf(*video_core, 0, memory, 0x00000000, 320, 240, BppSettings::bpp8),
        PlaneBuf(*video_core, 1, memory, 0x00020000, 320, 240, BppSettings::bpp4),
        PlaneBuf(*video_core, 2, memory, 0x00030000, 320, 240, BppSettings::bpp4),
        PlaneBuf(*video_core, 3, memory, 0x00040000, 320, 240, BppSettings::bpp4)
    };

    planes[0].set_enabled(true);
    planes[0].set_draw_order(0);
    planes[0].clear();
    for (size_t y = 0; y < 240; ++y) {
        for (size_t x = 0; x < 320; ++x) {
            planes[0].set_pixel(x,y, (y-x) & 0xff);
        }
    }

    size_t rect_ofs = 10;
    planes[1].set_enabled(true);
    planes[1].set_draw_order(1);
    planes[1].set_palette_1(32);
    planes[1].clear();
    planes[1].draw_rect(rect_ofs,rect_ofs,320-rect_ofs*2,240-rect_ofs*2,1);

    rect_ofs = 20;
    planes[2].set_enabled(true);
    planes[2].set_draw_order(2);
    planes[2].set_palette_1(64);
    planes[2].clear();
    planes[2].draw_rect(rect_ofs,rect_ofs,320-rect_ofs*2,240-rect_ofs*2,1);

    rect_ofs = 30;
    planes[3].set_enabled(true);
    planes[3].set_draw_order(3);
    planes[3].set_palette_1(96);
    planes[3].clear();
    planes[3].draw_rect(rect_ofs,rect_ofs,320-rect_ofs*2,240-rect_ofs*2,1);


    // Setting up sprite 0
    size_t sprite_0_base_addr = 0x00080000;
    std::array<SpriteBuf, 8> sprites = {
        SpriteBuf(*video_core, 0, memory, sprite_0_base_addr + 0x200*0, 32),
        SpriteBuf(*video_core, 1, memory, sprite_0_base_addr + 0x200*1, 32),
        SpriteBuf(*video_core, 2, memory, sprite_0_base_addr + 0x200*2, 32),
        SpriteBuf(*video_core, 3, memory, sprite_0_base_addr + 0x200*3, 32),

        SpriteBuf(*video_core, 4, memory, sprite_0_base_addr + 0x200*4, 32),
        SpriteBuf(*video_core, 5, memory, sprite_0_base_addr + 0x200*5, 32),
        SpriteBuf(*video_core, 6, memory, sprite_0_base_addr + 0x200*6, 32),
        SpriteBuf(*video_core, 7, memory, sprite_0_base_addr + 0x200*7, 32)
    };
    size_t idx = 0;
    for (auto &sprite: sprites) {
        // Set 16 color mode, draw order 0, enabled
        sprite.set_enabled(true);
        sprite.set_draw_order(idx+4);
        sprite.set_palette_1(8  + idx * 16);
        sprite.set_palette_2(16 + idx * 16);
        sprite.set_palette_3(48 + idx * 16);
        sprite.set_x(0   + idx*32);
        sprite.set_y(100 + idx*10);

        sprite.clear();
        sprite.draw_rect(0,0,32,32,1);
        sprite.fill_rect(12,12,8,8,2);
        sprite.fill_rect(14,14,4,4,3);
        ++idx;
    }

    // Creating a palette
    // A nice palette (from https://pixeljoint.com/forum/forum_posts.asp?TID=16247)
    SDL_Color palette32[] = {
        { 0,     0,    0,   255},
        { 34,   32,   52,   255},
        { 69,   40,   60,   255},
        {102,   57,   49,   255},
        {143,   86,   59,   255},
        {223,  113,   38,   255},
        {217,  160,  102,   255},
        {238,  195,  154,   255},
        {251,  242,   54,   255},
        {153,  229,   80,   255},
        {106,  190,   48,   255},
        { 55,  148,  110,   255},
        { 75,  105,   47,   255},
        { 82,   75,   36,   255},
        { 50,   60,   57,   255},
        { 63,   63,  116,   255},
        { 48,   96,  130,   255},
        { 91,  110,  225,   255},
        { 99,  155,  255,   255},
        { 95,  205,  228,   255},
        {203,  219,  252,   255},
        {255,  255,  255,   255},
        {155,  173,  183,   255},
        {132,  126,  135,   255},
        {105,  106,  106,   255},
        { 89,   86,   82,   255},
        {118,   66,  138,   255},
        {172,   50,   50,   255},
        {217,   87,   99,   255},
        {215,  123,  186,   255},
        {143,  151,   74,   255},
        {138,  111,   48,   255}
    };

    for(size_t i=0;i<ARRAY_SIZE(palette32);++i) {
        video_core->register_write((size_t)VideoCore::global_regs::palette_idx                , i);
        video_core->register_write((size_t)VideoCore::global_regs::palette_r                  , palette32[i].r);
        video_core->register_write((size_t)VideoCore::global_regs::palette_g                  , palette32[i].g);
        video_core->register_write((size_t)VideoCore::global_regs::palette_b                  , palette32[i].b);
    }
    //for(size_t i=0;i<16;++i) {
    //    video_core->register_write((size_t)VideoCore::global_regs::palette_idx                , i*2);
    //    video_core->register_write((size_t)VideoCore::global_regs::palette_r                  , 0);
    //    video_core->register_write((size_t)VideoCore::global_regs::palette_g                  , 0);
    //    video_core->register_write((size_t)VideoCore::global_regs::palette_b                  , 0);
    //    video_core->register_write((size_t)VideoCore::global_regs::palette_idx                , i*2+1);
    //    video_core->register_write((size_t)VideoCore::global_regs::palette_r                  , 255);
    //    video_core->register_write((size_t)VideoCore::global_regs::palette_g                  , 255);
    //    video_core->register_write((size_t)VideoCore::global_regs::palette_b                  , 255);
    //}


    bool terminate = false;
    PlaneOrSpriteBuf *selected_element = &sprites[0];
    while (!terminate) {
        uint32_t key;
        bool down_not_up;
        uint32_t modifiers;
        uint16_t pos;
        if (sdl_wrapper_kb_get_char(&key, &down_not_up, &modifiers)) {
            if (down_not_up) {
                switch (key) {
                    case SDL_KeyCode::SDLK_ESCAPE: terminate = true; break;
                    case SDL_KeyCode::SDLK_LEFT:
                        selected_element->set_x(selected_element->get_x()-1);
                    break;
                    case SDL_KeyCode::SDLK_RIGHT:
                        selected_element->set_x(selected_element->get_x()+1);
                    break;
                    case SDL_KeyCode::SDLK_UP:
                        selected_element->set_y(selected_element->get_y()-1);
                    break;
                    case SDL_KeyCode::SDLK_DOWN:
                        selected_element->set_y(selected_element->get_y()+1);
                    break;
                    case SDL_KeyCode::SDLK_1:
                    case SDL_KeyCode::SDLK_2:
                    case SDL_KeyCode::SDLK_3:
                    case SDL_KeyCode::SDLK_4:
                    case SDL_KeyCode::SDLK_5:
                    case SDL_KeyCode::SDLK_6:
                    case SDL_KeyCode::SDLK_7:
                    case SDL_KeyCode::SDLK_8:
                    {
                        size_t idx = key - SDL_KeyCode::SDLK_1;
                        if (modifiers & SDL_Keymod::KMOD_SHIFT) {
                            if (idx < planes.size()) {
                                if (modifiers & SDL_Keymod::KMOD_CTRL) {
                                    selected_element = &planes[idx];
                                } else {
                                    planes[idx].set_enabled(!planes[idx].get_enabled());
                                }
                            }
                        } else {
                            if (idx < sprites.size()) {
                                if (modifiers & SDL_Keymod::KMOD_CTRL) {
                                    selected_element = &sprites[idx];
                                } else {
                                    sprites[idx].set_enabled(!sprites[idx].get_enabled());
                                }
                            }
                        }
                    }
                    break;
                }
            }
        }
    }
    sdl_wrapper_terminate();
    free(memory);
}
