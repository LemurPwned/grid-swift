#include <libssh/libssh.h>
#include <stdlib.h>
#include <stdio.h>

#include "ssh_conn.h"

int establish_ssh_connection(const char *username, const char *server_address)
{
  ssh_session grid_session;
  unsigned char *hash = NULL;
  ssh_key srv_pubkey = NULL;
  size_t hlen;
  char buf[10];
  char *hexa;
  char *p;
  int cmp;
  int rc;
  int port = 22;
  int verbosity = SSH_LOG_PROTOCOL;

  grid_session = ssh_new();
  if (grid_session == NULL)
    exit(-1);
  ssh_options_set(grid_session, SSH_OPTIONS_HOST, server_address);
  ssh_options_set(grid_session, SSH_OPTIONS_USER, username);
  ssh_options_set(grid_session, SSH_OPTIONS_LOG_VERBOSITY, &verbosity);
  ssh_options_set(grid_session, SSH_OPTIONS_PORT, &port);

  rc = ssh_connect(grid_session);
  // verify_server(grid_session);
  if (rc != SSH_OK)
  {
    fprintf(stderr, "Error connecting to localhost: %s\n",
            ssh_get_error(grid_session));
    exit(-1);
  }

  int pass_res = authenticate_password(grid_session);
  const char *command = "ls -la";
  show_remote_processes(grid_session, command);

  ssh_disconnect(grid_session);
  ssh_free(grid_session);
  return 0;
}

int authenticate_password(ssh_session session)
{
  char *password;
  int rc;
  password = getpass("Enter your password: ");
  rc = ssh_userauth_password(session, NULL, password);
  if (rc == SSH_AUTH_ERROR)
  {
    fprintf(stderr, "Authentication failed: %s\n",
            ssh_get_error(session));
    return SSH_AUTH_ERROR;
  }
  return rc;
}

int verify_server(ssh_session sess)
{
  int state;
  state = ssh_is_server_known(sess);
  printf("State %d", state);
  switch (state)
  {
  case SSH_KNOWN_HOSTS_OK:
    printf("KNOWN HOST, SAFE SERVER...");
    break;
  default:
    printf("Undefined state, ending...");
    break;
  }
}

int show_remote_processes(ssh_session session, const char *cmd)
{
  ssh_channel channel;
  int rc;
  char buffer[256];
  int nbytes;
  channel = ssh_channel_new(session);
  if (channel == NULL)
    return SSH_ERROR;
  rc = ssh_channel_open_session(channel);
  if (rc != SSH_OK)
  {
    ssh_channel_free(channel);
    return rc;
  }
  rc = ssh_channel_request_exec(channel, cmd);
  if (rc != SSH_OK)
  {
    ssh_channel_close(channel);
    ssh_channel_free(channel);
    return rc;
  }
  nbytes = ssh_channel_read(channel, buffer, sizeof(buffer), 0);
  while (nbytes > 0)
  {
    if (write(1, buffer, nbytes) != (unsigned int)nbytes)
    {
      ssh_channel_close(channel);
      ssh_channel_free(channel);
      return SSH_ERROR;
    }
    nbytes = ssh_channel_read(channel, buffer, sizeof(buffer), 0);
  }

  if (nbytes < 0)
  {
    ssh_channel_close(channel);
    ssh_channel_free(channel);
    return SSH_ERROR;
  }
  ssh_channel_send_eof(channel);
  ssh_channel_close(channel);
  ssh_channel_free(channel);
  return SSH_OK;
}

int scp_file(char *filename, char *user, char *server, char *remote_dir)
{
  /* remote to local copy */
  char command[200];
  // sprintf(command, "scp -P 32768 %s@%s:%s %s", user, server, remote_dir, filename);
  sprintf(command, "scp %s@%s:%s %s", user, server, remote_dir, filename);
  printf("executing %s...\n", command);

  system(command);
  return 0;
}