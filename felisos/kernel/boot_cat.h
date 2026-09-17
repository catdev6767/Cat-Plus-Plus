/* Auto-generated */
#ifndef BOOT_CAT_H
#define BOOT_CAT_H

static const char SysCat_src[] = "# SysCat — init process\nmeow \"SysCat: khoi dong FelisOS...\"\nmeow \"\"\nmeow \"SysCat: nap shell\"\nexec(\"/boot/sh.cat\")\nmeow \"SysCat: shell ket thuc\"\nmeow \"SysCat: system halt\"\n";

static const char sh_cat_src[] = "# sh.cat — FelisOS Shell\nmeow \"FelisOS Shell v0.1\"\nmeow \"Go 'help' de xem lenh\"\nmeow \"\"\n\npaw running = nod\nknead running\n    paw cmd = readline(\"felis:/$ \")\n    sniff cmd == \"exit\"\n        running = shake\n    swat\n        sniff cmd == \"\"\n        swat\n            exec(cmd)\n\nmeow \"Bye!\"\n";

#endif
