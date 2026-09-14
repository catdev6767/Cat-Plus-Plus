#include <stdint.h>
#include "catpp_rt.h"



long square(long n) {
    return (n * n);
}

int catpp_main(void) {
    catpp_print_str("Hello from Cat++ in kernel!");
    long x = 10;
    long y = 20;
    catpp_print((x + y));
    long i = 0;
    while ((i < 5)) {
        catpp_print(i);
        i += 1;
    }
    catpp_print(square(7));
    return 0;
}
