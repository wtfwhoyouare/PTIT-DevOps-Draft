FROM mariadb:10.11

# Cau hinh CO Y de lo:
#  - secure_file_priv='' -> LOAD_FILE / INTO OUTFILE doc-ghi moi noi
#  - local_infile bat
COPY lab.cnf /etc/mysql/conf.d/lab.cnf

# init.sql chay tu dong khi container khoi tao lan dau (tao 2 DB + seed)
COPY init.sql /docker-entrypoint-initdb.d/init.sql

# Wrapper entrypoint: mo quyen ghi cho thu muc chia se (shared_files)
# de MySQL (user mysql) co the ghi web shell qua INTO OUTFILE.
COPY fix-perms-entrypoint.sh /usr/local/bin/fix-perms-entrypoint.sh
RUN chmod +x /usr/local/bin/fix-perms-entrypoint.sh
ENTRYPOINT ["fix-perms-entrypoint.sh"]
CMD ["mariadbd"]
