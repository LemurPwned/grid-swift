
#if !defined(UTILS)
#define UTILS
#include "../structure_defs/job_def.h"

void extract_basename(char *filepath, char *basename);
void replace_space(const char *input, char *result);
char *readFile(char *fileName);
int extract_job_number(char *sbatch_output);
void log_to_file(FILE *log_file, char type, char *msg);
void pipe_opener(FILE *reuslable_file, char *command, char *output, int silent);
void get_status_jobs(struct job_info jobs[], int job_size);
void read_jobs_from_file(JOB_INF *jobs, char *filename, int job_num);
void save_jobs_to_file(JOB_INF jobs[], int job_num);
#endif // UTILS
