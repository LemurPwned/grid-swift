#include <libssh/libssh.h> 


int authenticate_password(ssh_session session);
int verify_server(ssh_session sess);
int show_remote_processes(ssh_session session, const char* cmd);
