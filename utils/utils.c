
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <regex.h>
#include <stdbool.h>
#include "../utils/utils.h"

char *readFile(char *fileName)
{
    FILE *file = fopen(fileName, "r");
    char *filetext;
    size_t n = 0;
    int c;

    if (file == NULL)
        return NULL; //could not open file
    filetext = malloc(1000);
    while ((c = fgetc(file)) != EOF)
    {
        filetext[n++] = (char)c;
    }
    // terminate on null character
    filetext[n] = '\0';

    return filetext;
}

void remove_spaces(const char *input, char *result)
{
    int i, j = 0;
    for (i = 0; input[i] != '\0'; i++)
    {
        if (!isspace((unsigned char)input[i]))
        {
            result[j++] = input[i];
        }
    }
    result[j] = '\0';
}

void replace_space(const char *input, char *result)
{
    int i, j = 0;
    for (i = 0; input[i] != '\0'; i++)
    {
        result[i] = isspace((unsigned char)input[i]) ? '_' : input[i];
    }
    result[strlen(input)] = '\0';
}

void extract_basename(char *filepath, char *basename)
{
    for (int i = strlen(filepath); i > 0; i--)
    {
        if (filepath[i] == '/')
        {
            int string_size = strlen(filepath) - i;
            for (int j = 0; j < string_size; j++)
            {
                basename[j] = filepath[i + 1 + j];
            }
            return;
        }
    }
}

void save_jobs_to_file(JOB_INF jobs[], int job_num)
{

    char *filename;
    sprintf(filename, "JOBS_%d", job_num);
    FILE *fp = fopen(filename, 'w');
    if (fp == NULL)
    {
        perror("Cannot save jobs due to file read error");
        exit(-1);
    }
    for (int i = 0; i < job_num; i++)
    {
        fprintf(fp, "%i;%s%s", jobs[i].job_no,
                jobs[i].job_timestamp,
                jobs[i].run_time);
    }
    fclose(fp);
}

void read_jobs_from_file(JOB_INF *jobs, char *filename, int job_num)
{
    FILE *fp;
    char *line = NULL;
    size_t len = 0;
    ssize_t read;
    int num, i = 0;

    fp = fopen(filename, "r");
    if (fp == NULL)
        exit(EXIT_FAILURE);
    while ((read = getline(&line, &len, fp)) != -1)
    {
        num = strtol(line, NULL, 10);
        jobs[i].job_no = num;
        printf("%d\n", jobs[i].job_no);
        i++;
    }
    printf("LEFTOVER %d\n", i);
    fclose(fp);
    if (line)
        free(line);
}
void get_status_jobs(JOB_INF jobs[], int job_size)
{
    FILE *fp;
    char output[300];

    pipe_opener(fp, "cat queue.txt |  cut -d ' ' -f 11", output, 0);
    char *line = NULL;
    ssize_t read;
    size_t len = 0;
    int j = 0;
    int a;
    while ((read = getline(&line, &len, fp)) != -1)
    {
        //     a = strtol(line, NULL, 10);
        //     // jobs[j].job_no = a;
        //     j++;
        //     if (j > job_size)
        //         break;
    }
    // fclose(fp);
    // if (line)
    // free(line);
    for (int i = 0; i < job_size; i++)
    {
        // printf("JOB NO: %d\n", jobs[i].job_no);
    }
}

int extract_job_number(char *sbatch_output)
{
    char *regex_string = "([0-9]+)";

    // sbatch: Submitted batch job 99999999
    regex_t regex_compiled;
    regmatch_t pmatch[1];
    int job_no;

    if (regcomp(&regex_compiled, regex_string, REG_EXTENDED))
    {
        printf("Could not compile regex\n");
        regfree(&regex_compiled);
        return false;
    }
    int match = regexec(&regex_compiled, sbatch_output, 1, pmatch, 0);
    regfree(&regex_compiled);
    if (match)
    {
        perror("extracted batch is not a valid batch output");
        return false;
    }
    else
    {
        printf("matched from %d (%c) to %d (%c)\n",
               pmatch[0].rm_so,
               sbatch_output[pmatch[0].rm_so],
               pmatch[0].rm_eo,
               sbatch_output[pmatch[0].rm_eo - 1]);
    }
    int offset = pmatch[0].rm_eo - pmatch[0].rm_so;
    char job_no_str[offset];
    strncpy(job_no_str, sbatch_output + pmatch[0].rm_so, pmatch[0].rm_eo);
    job_no_str[offset] = '\0';
    job_no = strtol(job_no_str, NULL, 10);
    return job_no;
}

void log_to_file(FILE *log_file, char type, char *msg)
{
    if (log_file != NULL)
    {
        time_t now = time(NULL);
        char *time_str = ctime(&now);
        time_str[strlen(time_str) - 1] = '\0';
        fprintf(log_file, "[%c]-[%s]: %s\n", type, time_str, msg);
    }
    else
    {
        perror("LOG FILE is NULL");
    }
}

void list_jobs_in_progress(FILE *source)
{
    // first get the jobs from the file
}
void pipe_opener(FILE *reusable_pipe, char *command, char *output, int silent)
{
    if (silent)
    {
        system(command);
    }
    else
    {
        reusable_pipe = popen(command, "r");
        if (reusable_pipe == NULL)
        {
            perror("Failed to open fipe");
            return;
        }

        fgets(output, 200, reusable_pipe);

        int status = pclose(reusable_pipe);
        if (status == -1)
        {
            perror("An error occurred while pipe proces was closed");
        }
    }
}
