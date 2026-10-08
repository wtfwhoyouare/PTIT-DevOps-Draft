#!/bin/bash
# Mo quyen ghi cho thu muc chia se de MySQL co the ghi file (INTO OUTFILE).
# Day la cau hinh CO Y de lo cho lab (minh hoa Writing files -> web shell).
mkdir -p /var/lib/mysql-files
chmod 1777 /var/lib/mysql-files || true

# Chuyen tiep sang entrypoint goc cua image mariadb
exec docker-entrypoint.sh "$@"
