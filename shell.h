
#if !defined(SHELL)
#define SHELL

#include "structure_defs/config_def.h"
#include "parsers/json_readers.h"
#include "parsers/cartesian.h"

int queue_script_writer(OOMMF_CONFIG *conf_spec, char filepath[], char parameter_string[], char mif_path[]);
int oommf_task_executor(char *config_file, USER_DATA *ud);
void remove_spaces(const char *input, char *result);
void create_dir(char directory_path[], int force_removal);
int extract_job_number(char *sbatch_output);
#endif // SHELL
