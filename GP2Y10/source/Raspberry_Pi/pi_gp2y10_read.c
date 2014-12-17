#include <stdio.h>
#include <unistd.h>
#include <getopt.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <termios.h>
#include <sys/time.h>

#include "pi_gp2y10_read.h"

#undef DEBUG
//#define DEBU

int pi_tty_init(void) {
	int fd;
	fd = open("/dev/ttyAMA0", O_RDONLY | O_NOCTTY);
	if (fd < 0) {
		printf("failed to open UART port: %s\n", strerror(errno) );
		return GP2Y10_ERROR_SERIAL;
	}
	return GP2Y10_SUCCESS;
}

int read_gp2y() {
	struct termios term;
	struct timeval timeout;
	unsigned char buff[32];
	fd_set rd_set;
	int fd, rc, i, total = 0;

	fd = open("/dev/ttyAMA0", O_RDONLY | O_NOCTTY);
	if (fd < 0) {
		printf("failed to open UART port: %s\n", strerror(errno) );
		return GP2Y10_ERROR_SERIAL;
	}

	tcgetattr(fd, &term);
	term.c_cflag = B2400 | CS8 | CLOCAL | CREAD;
	term.c_iflag = IGNPAR;
	term.c_oflag = 0;
	term.c_lflag = 0;
	tcflush(fd, TCIFLUSH);
	tcsetattr(fd, TCSANOW, &term);

	/* data should be arriving in 100ms */
	timeout.tv_sec = 0;
	timeout.tv_usec = 100000;	/* 100 ms */
	FD_ZERO(&rd_set);
	FD_SET(fd, &rd_set);
	rc = select(fd + 1, &rd_set, NULL, NULL, &timeout);
	if (rc <= 0) {	/* timeout or error */
		printf("no response from dust sensor, please check "
				"your hardware settings.\n");
		close(fd);
		return GP2Y10_ERROR_TIMEOUT;
	} else {
		if (!FD_ISSET(fd, &rd_set) ) {
			printf("Ooops, something weird happend ...\n");
			close(fd);
			return GP2Y10_ERROR_TIMEOUT;
		}
	}

	while (total < sizeof(buff) ) {
		rc = read(fd, buff + total, sizeof(buff) - total);
		if (rc <= 0) {
			printf("failed to read data from UART: %s\n", strerror(errno) );
			close(fd);
			return GP2Y10_ERROR_TIMEOUT;
		}

		total += rc;
	}

	close(fd);

#ifdef DEBUG
	printf("Received %d bytes:\n", total);
	for (i = 0; i < total; i++) {
		printf("%02x ", buff[i] );
		if ( (i % 16) == 15)
			printf("\n");
	}
#endif

	/* at least 7 bytes */
	if (total < 8)
		return GP2Y10_ERROR_CHECKSUM;

	/* since the dust sensor output data continuously, we need to lock the
	 * preamble and termination to retrieve meaningful data.
	 */
	i = 0;
loop:
	while (buff[i] != 0xaa) {
		if (++i > (total - 7) )
			return GP2Y10_ERROR_CHECKSUM;	/* no valid data available */
	}

	if (buff[++i+5] != 0xff)
		goto loop;

	/* sanity check */
	if ( ( (buff[i] + buff[i+1] + buff[i+2] +
					buff[i+3]) & 0xff) != buff[i+4] )
		goto loop;

	return ( (buff[i] << 8) | buff[i+1] );
}


int pi_gp2y10_read(int sensor, int sample, float* density) {

	if (pi_tty_init() < 0) {
		return GP2Y10_ERROR_SERIAL;
	}

	float pm25;
	unsigned int data;
	int i, nr_samples;

	pm25 = 0;
	nr_samples = 0;
	for (i = 0; i < sample; i++) {
		data = read_gp2y();
		if (data >= 0)
			nr_samples++;
		else
			data = 0;

		pm25 += data;
	}

	*density = ( (pm25 / nr_samples) * 5 * 100 / 1024);

	return GP2Y10_SUCCESS;
}
