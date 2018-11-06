
#if !defined(UTILS)
#define UTILS
#include "../structure_defs/job_def.h"

void extract_basename(char *filepath, char *basename);
void replace_space(const char *input, char *result);
char *readFile(char *fileName);
int extract_job_number(char *sbatch_output);
void log_to_file(FILE *LOG_FILE, char type, char *msg);
void pipe_opener(FILE *__REUSABLE_PIPE__, char *command, char **output, int silent);
void get_status_jobs(JOB_INF jobs[], int job_size);
#endif // UTILS
