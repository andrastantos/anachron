#include "event_counters.h"
#include "platform.h"

void event_select_event(size_t counter, uint32_t event) {
    switch (counter) {
        case 0: csr_event_sel<0>(event); break;
        case 1: csr_event_sel<1>(event); break;
        case 2: csr_event_sel<2>(event); break;
        case 3: csr_event_sel<3>(event); break;
        case 4: csr_event_sel<4>(event); break;
        case 5: csr_event_sel<5>(event); break;
        case 6: csr_event_sel<6>(event); break;
        case 7: csr_event_sel<7>(event); break;
        default: return;
    }
}

uint32_t event_get_cnt(size_t counter) {
    switch (counter) {
        case 0: return csr_event_cnt<0>();
        case 1: return csr_event_cnt<1>();
        case 2: return csr_event_cnt<2>();
        case 3: return csr_event_cnt<3>();
        case 4: return csr_event_cnt<4>();
        case 5: return csr_event_cnt<5>();
        case 6: return csr_event_cnt<6>();
        case 7: return csr_event_cnt<7>();
        default: return 0;
    }
}

void event_enable_events() {
    csr_event_enable(1);
}

void event_disable_events() {
    csr_event_enable(0);
}


