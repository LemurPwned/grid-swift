#include <assert.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../utils/utils.h"
#include "../structure_defs/job_def.h"

void assert_file_or_directory_existence(char *filename)
{
    if (access(filename, R_OK | W_OK))
    {
        perror("Either the file does not exist or you don't have W/R permisssions");
        exit(-1);
    }
}

void test_regex()
{
    char *ex_regex = "sbatch: Submitted batch job 123456789";
    int result = extract_job_number(ex_regex);
    assert(result == 123456789);
}

void test_logging()
{
    FILE *fp;
    // create file
    char *test_filename = "asserts/assert.log";
    fp = fopen(test_filename, "w");
    assert(fp != NULL);
    write(fp, "TEST", sizeof("TEST"));
    close(fp);
    // use it as log file in the append mode
    fp = fopen(test_filename, "a");
    assert(fp != NULL);
    log_to_file(fp, 'I', "THIS IS A TEST MESSAGE");
    assert_file_or_directory_existence(test_filename);
    /*
    TODO:
        Clean up the file by removing it
        Check the contents of the file.
    */
}

void test_popen()
{
#ifdef __unix__
    /*
    popen is not defined for all linux-type system
    thats probs the most reliable check we can have
    */
    char output[200]; // 200 should be enough but crash if not
    FILE *rp;         // file handler is provided but actual pipe is opened in the function
    pipe_opener(rp, "echo HELLO", output, 0);
    // make sure the pipe returns proper stuff when not in the silent mode
    assert(!strcmp(output, "HELLO\n"));
#else
    perror("Not an UNIX type system");
#endif
}

void test_job_extraction()
{
    char job_size[20];
    FILE *fp;
    pipe_opener(fp, "cat queue.txt |cut -d ' ' -f 11 | wc -l", job_size, 0);
    int job_num = strtol(job_size, NULL, 10);
    JOB_INF jobs[12];
    read_jobs_from_file(jobs, "nq.txt", 13);
    printf("JOB NO: %d\n", 12);
    for (int i = 0; i < 13; i++)
    {
        printf("%d\n", jobs[i].job_no);
    }

    // get_status_jobs(jobs, job_num);
}
int main(int argc, char *argv[])
{
    test_regex();
    test_logging();
    test_popen();
    test_job_extraction();
    return 0;
}