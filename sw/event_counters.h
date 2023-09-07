#pragma once

#include <stdint.h>
#include <stddef.h>

void event_select_event(size_t counter, uint32_t event);
uint32_t event_get_cnt(size_t counter);
void event_enable_events();
void event_disable_events();
