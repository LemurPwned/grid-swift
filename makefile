OBJS=shell.o ssh_conn.o argument_parser.o cJSON.o

all: $(OBJS)
	gcc $(OBJS) -o client -lssh

shell.o: shell.c
	gcc -c shell.c 

ssh_conn.o: ssh_conn.c
	gcc -c ssh_conn.c

argument_parser.o: argument_parser.c shell.o
	gcc -c argument_parser.c

cJSON.o: cJSON.c
	gcc -c cJSON.c

test: cJSON.o test_json.c 
	gcc cJSON.o test_json.c -o json 

	