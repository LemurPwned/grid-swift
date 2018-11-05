
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
        return false;
    }
    int match = regexec(&regex_compiled, sbatch_output, 1, pmatch, 0);
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

void log_to_file(FILE *LOG_FILE, char type, char *msg)
{
    if (LOG_FILE != NULL)
    {
        time_t now = time(NULL);
        char *time_str = ctime(&now);
        time_str[strlen(time_str) - 1] = '\0';
        fprintf(LOG_FILE, "[%c]-[%s]: %s\n", type, time_str, msg);
    }
    else
    {
        perror("LOG FILE is NULL");
    }
}

void pipe_opener(FILE *__REUSABLE_PIPE__, char *command, char **output, int silent)
{
    if (silent)
    {
        system(command);
    }
    else
    {
        __REUSABLE_PIPE__ = popen(command, "r");
        if (__REUSABLE_PIPE__ == NULL)
        {
            perror("Failed to open fipe");
        }

        fgets(output, 200, __REUSABLE_PIPE__);

        int status = pclose(__REUSABLE_PIPE__);
        if (status == -1)
        {
            perror("An error occurred while pipe proces was closed");
        }
    }
}
