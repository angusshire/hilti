/* $Id$
 *
 * Configuration mechanism for the HILTI framework and runtime.
 *
 */

#include "hilti.h"

// FIXME: Maybe it would be better to have the user create a config object and use it,
// instead of having a singleton one.

static hlt_config current_config;

void __hlt_config_init()
{
    current_config.num_workers = 2;
    current_config.time_idle = 0.1;
    current_config.time_terminate = 1.0;
    current_config.stack_size = 268435456;
    current_config.debug_out = stderr;
    current_config.debug_streams = 0;
    current_config.profiling = 0;
    current_config.vid_schedule_min = 1;
    current_config.vid_schedule_max = 101;
    current_config.core_affinity = "DEFAULT";
}

const hlt_config* hlt_config_get()
{
    return &current_config;
}

void hlt_config_set(const hlt_config* new_config)
{
    bool init_prof =  (new_config->profiling && ! current_config.profiling);

    current_config = *new_config;

    if ( init_prof )
        // Initialize profiling.
        __hlt_profiler_init();
}