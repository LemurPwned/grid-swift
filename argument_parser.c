#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <argp.h>

#include "shell.h"

#define MAX_ARGUMENT_STR_LEN 200

const char *argp_program_version = "PLGRiD Shell v1.0";
const char *argp_program_bug_address = "jakubmj@student.agh.edu.pl";
static char doc[] = "PLGRID V.A.S.P. interface";
static char args_doc[] = "[FILENAME]...";


struct arguments{
    char *server;
    char *simtype;
    char *username;
    char *conf_file;
};

static struct argp_option options[] = { 
    { "simulation_type", 's', "SIM_TYPE", 0, "Simulation type: V.A.S.P. or OOMMF"},
    { "config_file", 'f', "CONF_FILE", 0, "Config file with sim setup - json type"},
    { "username", 'u', "USERNAME", 0, "Username for remote ssh connection"},
    { "server", 0x100, "SERVERNAME", 0, "Servername for remote ssh connection"},
    { 0 }
};


static error_t parse_opt(int key, char *arg, struct argp_state *state) {
    struct arguments *arguments = state->input;
    // printf("KEY %s", key);
    switch (key) {
    case 0x100: arguments->server = arg; break;
    case 's': arguments->simtype = arg; break;
    case 'u': arguments->username = arg; break;
    case 'f': arguments->conf_file = arg; break;
    case ARGP_KEY_ARG: return 0;
    default: return ARGP_ERR_UNKNOWN;
    }   
    return 0;
}

static struct argp argp = { options, parse_opt, args_doc, doc };

int main(int argc, char **argv)
{
    struct arguments arguments;
    // default options
    arguments.simtype = "o";
    arguments.username = "lemur";
    arguments.conf_file = "conf.json";

    argp_parse(&argp, argc, argv, 0, 0, &arguments);
    printf("READ PARAMETERS: %s, %s, %s\n", arguments.username, arguments.server, arguments.conf_file);
    oommf_task_executor(arguments.conf_file);
    return 0;
}