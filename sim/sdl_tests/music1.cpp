#include <SDL2/SDL.h>
#include <SDL2/SDL_audio.h>
#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#define PI2 6.28318530718

float duration = 0;
float freq = 440;

void callback(void *userdata, Uint8 *stream, int len)
{
	short *snd = (short*)stream;
	len /= sizeof(*snd);
	for (int i = 0; i < len; i++) //Fill array with frequencies, mathy-math stuff
	{
		snd[i] = 32000 * sin(duration);

		duration += freq * PI2 / 48000.0;
		if (duration >= PI2)
			duration -= PI2;
	}
}

int main(int argc, char **argv)
{

	srand(time(NULL));

	SDL_Init(SDL_INIT_AUDIO);
	SDL_AudioSpec spec, aspec; // the specs of our piece of "music"
	SDL_zero(spec);
	spec.freq = 48000; //declare specs
	spec.format = AUDIO_S16SYS;
	spec.channels = 1;
	spec.samples = 4096;
	spec.callback = callback;
	spec.userdata = NULL;

	//Open audio, if error, print
	int id;
	if ((id = SDL_OpenAudioDevice(NULL, 0, &spec, &aspec, SDL_AUDIO_ALLOW_ANY_CHANGE)) <= 0)
	{
		fprintf(stderr, "Couldn't open audio: %s\n", SDL_GetError());
		exit(-1);
	}

	/* Start playing, "unpause" */
	SDL_PauseAudioDevice(id, 0);

	while (true)
	{
		for (freq = 440; freq < 880; freq += 2)
			SDL_Delay(5);
		for (freq = 870; freq > 450; freq -= 2)
			SDL_Delay(5);
	}

}
