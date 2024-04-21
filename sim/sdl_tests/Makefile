LIBS = -lSDL2 -lSDL2_image
CXXFLAGS = -g -O0
CXX = g++

#all: sdl1.elf
all: music1.elf

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

%.elf: %.o
	$(CXX)  $^ $(CXXFLAGS) $(LIBS) -o $@

clean:
	rm *.o *.elf
