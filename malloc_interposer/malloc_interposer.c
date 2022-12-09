/* Example of a library interposer: interpose on malloc().
 * gcc -D_GNU_SOURCE -fPIC -O2 -Wall -o malloc_interposer.so -shared malloc_interposer.c -ldl
 * setenv LD_PRELOAD $cwd/malloc_interposer.so
 * run the app
 */

#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <fcntl.h>

int LOG_FD = 0;
#define WRITE_LOG_SIZE  (64 * 1024)

static void * (*real_malloc)() = NULL;
static void * (*real_calloc)() = NULL;
static int    (*real_posix_memalign)() = NULL;
static void * (*real_aligned_alloc)() = NULL;
static void * (*real_realloc)() = NULL;
static int ret;

static char writeBuf[WRITE_LOG_SIZE];   // Buffering for write() syscall
static int writePtr = 0;                // Points to the first free slot

pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;;

/*
 * Buffers calls to write() for speeding up log output
*/
static void WRITE(int fd, const void *buf, size_t count)
{
    pthread_mutex_lock(&lock);
    if (writePtr + count > WRITE_LOG_SIZE)
    {
        // Flush the buffer
        ret = write(LOG_FD, writeBuf, writePtr);
        writePtr = 0;
    }
    memcpy(&writeBuf[writePtr], buf, count);
    writePtr += count;
    pthread_mutex_unlock(&lock);
}

static inline void printChar(char c)
{
    WRITE(LOG_FD, &c, sizeof(char));
}

void bye()
{
    while(writePtr != 0) {
        ret = write(LOG_FD, writeBuf, writePtr);
        writePtr -= ret;
    }
    
}

void init()
{
    atexit (bye);
    pid_t x = getpid();
    char filename[1024] = "malloc_";
    char buf[1024] = {0};

    int digits = 0, r;

    while (x > 0)
    {
        r = x % 10;
        x = x / 10;
        buf[digits++] = ('0' + r);
    }

    int i = 0, j = digits - 1;
    while (i < j)
    {
        char tmp = buf[i];
        buf[i] = buf[j];
        buf[j] = tmp;
        ++i; --j;
    }

    strcat(filename, buf);
    strcat(filename, ".txt");
    LOG_FD = open(filename, O_RDWR | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR);
}

void printNumber(size_t x)
{
    char buf[1024];
    if (x == 0)
    {
        buf[0] = '0';
        WRITE(LOG_FD, buf, sizeof(char));
        return;
    }

    int digits = 0, r;

    while (x > 0)
    {
        r = x % 10;
        x = x / 10;
        buf[digits++] = ('0' + r);
    }

    int i = 0, j = digits - 1;
    while (i < j)
    {
        char tmp = buf[i];
        buf[i] = buf[j];
        buf[j] = tmp;
        ++i; --j;
    }

    WRITE(LOG_FD, buf, digits);
}

void *malloc(size_t size) {

    // Log request size to LOG_FD
    const char msg[] = "malloc ";
	WRITE(LOG_FD, msg, sizeof(msg) - 1);
    printNumber(size);
    printChar('\n'); 

    if(!real_malloc) {
        init();
        real_malloc = (void *(*)()) dlsym(RTLD_NEXT, "malloc");
    }

    void *mem = real_malloc(size);

    // printNumber((size_t)mem);
    // printChar('\n');
    return mem;
}

void *calloc(size_t number, size_t size) {

    // Log request size to LOG_FD
    const char msg[] = "calloc ";
	WRITE(LOG_FD, msg, sizeof(msg) - 1);
    printNumber(size * number);
    printChar('\n'); 

    if(!real_calloc)
        real_calloc = (void *(*)()) dlsym(RTLD_NEXT, "calloc");

    void *mem = real_calloc(number, size);
    // printNumber((size_t)mem);
    // printChar('\n');
    return mem;
}

int posix_memalign(	void **ptr, size_t alignment, size_t size)
{
    // Log request size to LOG_FD
    const char msg[] = "posix_memalign ";
	WRITE(LOG_FD, msg, sizeof(msg) - 1);
    printNumber(size);
    printChar('\n'); 

    if (!real_posix_memalign)
        real_posix_memalign = (int (*)()) dlsym(RTLD_NEXT, "posix_memalign");
    
    int val = real_posix_memalign(ptr, alignment, size);
    // printNumber((size_t)*ptr);
    // printChar('\n');
    return val;
}

void *aligned_alloc(size_t alignment, size_t size)
{
    // Log request size to LOG_FD
    const char msg[] = "aligned_alloc ";
	WRITE(LOG_FD, msg, sizeof(msg) - 1);
    printNumber(size);
    printChar('\n'); 

    if (!real_aligned_alloc)
        real_aligned_alloc = (void *(*)()) dlsym(RTLD_NEXT, "aligned_alloc");
    
    void *mem = real_aligned_alloc(alignment, size);
    // printNumber((size_t)mem);
    // printChar('\n');
    return mem;
}

void *realloc(void *ptr, size_t size)
{
    // Log request size to LOG_FD
    const char msg[] = "realloc ";
	WRITE(LOG_FD, msg, sizeof(msg) - 1);
    printNumber(size);
    printChar('\n');

    if (!real_realloc)
        real_realloc = (void *(*)()) dlsym(RTLD_NEXT, "realloc");
    
    void *mem = real_realloc(ptr, size);
    // printNumber((size_t)mem);
    // printChar('\n');
    return mem;
}
