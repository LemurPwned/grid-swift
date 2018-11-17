#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <argp.h>
#include <string.h>

#include "shell.h"
#include "structure_defs/config_def.h"

#define MAX_ARGUMENT_STR_LEN 200

const char *argp_program_version = "PLGRiD Shell v1.0";
const char *argp_program_bug_address = "jakubmj@student.agh.edu.pl";
static char doc[] = "PLGRID CLI interface";
static char args_doc[] = "[FILENAME]...";

struct arguments
{
    char *server;
    char *simtype;
    char *username;
    char *conf_file;
};

static struct argp_option options[] = {
    {"config_file", 'f', "CONF_FILE", 0, "Config file with sim setup - json type"},
    {"username", 'u', "USERNAME", 0, "Username for remote ssh connection"},
    {"server", 's', "SERVERNAME", 0, "Servername for remote ssh connection"},
    {0}};

static error_t parse_opt(int key, char *arg, struct argp_state *state)
{
    struct arguments *arguments = state->input;
    switch (key)
    {
    case 's':
        arguments->server = arg;
        break;
    case 'u':
        arguments->username = arg;
        break;
    case 'f':
        arguments->conf_file = arg;
        break;
    case ARGP_KEY_ARG:
        return 0;
    default:
        return ARGP_ERR_UNKNOWN;
    }
    return 0;
}

static struct argp argp = {options, parse_opt, args_doc, doc};

int main(int argc, char **argv)
{
    struct arguments arguments;
    // default options
    arguments.username = "root";
    arguments.conf_file = "config/conf.json";
    arguments.server = "localhost";

    USER_DATA ud = {0};
    strcpy(ud.username, arguments.username);
    strcpy(ud.hostname, arguments.server);

    argp_parse(&argp, argc, argv, 0, 0, &arguments);
    printf("READ PARAMETERS: %s, %s, %s\n", ud.username, ud.hostname, arguments.conf_file);
    oommf_task_executor(arguments.conf_file, &ud);
    // upload the file to the queue system along with the scripts
    // scp_file("testfile.pbs", arguments.username, arguments.server, "~/sim-dir");
    return 0;
}