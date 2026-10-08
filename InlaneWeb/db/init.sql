-- ============================================================================
--  IlFreight Logistics — Lab SQLi  |  init.sql
--  Tao 2 database: ilfreight (app chinh) + dev (muc tieu enumeration)
--  Seed du lieu that + flags theo tung ky thuat khai thac.
-- ============================================================================

-- ------------------------------------------------------------------
--  Privilege: root duoc phep ket noi tu moi host, co FILE privilege
--  (FILE la mac dinh cua root; ta khang dinh lai cho ro rang).
-- ------------------------------------------------------------------
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
GRANT FILE ON *.* TO 'root'@'%';
FLUSH PRIVILEGES;

-- ============================================================================
--  DATABASE: ilfreight  (web app chay o day)
-- ============================================================================
CREATE DATABASE IF NOT EXISTS ilfreight CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ilfreight;

-- ---- users ----------------------------------------------------------------
CREATE TABLE users (
    id             INT NOT NULL AUTO_INCREMENT,
    username       VARCHAR(100) UNIQUE NOT NULL,
    password       VARCHAR(255) NOT NULL,   -- luu cleartext (bad practice CO Y)
    email          VARCHAR(150),
    role           VARCHAR(20) DEFAULT 'customer',
    api_key        VARCHAR(64),
    remember_token VARCHAR(64),
    PRIMARY KEY (id)
);

INSERT INTO users (username, password, email, role, api_key) VALUES
('admin',   'p@ssw0rd',    'admin@ilfreight.local',  'admin',    'ILF-ADM-9f3c1a77e2b04d55'),
('jsmith',  'Spring2024!', 'jsmith@ilfreight.local', 'customer', 'ILF-CUS-1b2c3d4e5f60718'),
('awong',   'Hongkong88',  'awong@ilfreight.local',  'customer', 'ILF-CUS-aa11bb22cc33dd44'),
('mgarcia', 'Barca#2010',  'mgarcia@ilfreight.local','staff',    'ILF-STF-99887766554433');

-- ---- ports (bang tra cuu cong khai — giong bai giang) ----------------------
CREATE TABLE ports (
    id      INT NOT NULL AUTO_INCREMENT,
    code    VARCHAR(10),
    city    VARCHAR(100),
    country VARCHAR(100),
    volume  DECIMAL(6,2),
    PRIMARY KEY (id)
);

INSERT INTO ports (code, city, country, volume) VALUES
('CN SHA', 'Shanghai',  'China',        37.13),
('SG SIN', 'Singapore', 'Singapore',    36.60),
('CN SHE', 'Shenzhen',  'China',        23.97),
('CN NGB', 'Ningbo',    'China',        27.53),
('AE DXB', 'Dubai',     'UAE',          15.73),
('BR SSZ', 'Santos',    'Brazil',        3.60),
('NL RTM', 'Rotterdam', 'Netherlands',  14.35),
('US LAX', 'Los Angeles','USA',          9.20);

-- ---- shipments (van don) ---------------------------------------------------
CREATE TABLE shipments (
    id          INT NOT NULL AUTO_INCREMENT,
    tracking_no VARCHAR(30) UNIQUE,
    port_code   VARCHAR(10),
    status      VARCHAR(40),
    customer_id INT,
    PRIMARY KEY (id)
);

INSERT INTO shipments (tracking_no, port_code, status, customer_id) VALUES
('ILF1042CN', 'CN SHA', 'In Transit',     2),
('ILF1043SG', 'SG SIN', 'At Port',        2),
('ILF1044AE', 'AE DXB', 'Customs Hold',   3),
('ILF1045NL', 'NL RTM', 'Delivered',      3),
('ILF1046US', 'US LAX', 'Out for Delivery',4);

-- ---- comments (binh luan don hang) ----------------------------------------
CREATE TABLE comments (
    id          INT NOT NULL AUTO_INCREMENT,
    shipment_id INT,
    user_id     INT,
    content     TEXT,
    created_at  DATETIME DEFAULT NOW(),
    PRIMARY KEY (id)
);

INSERT INTO comments (shipment_id, user_id, content) VALUES
(1, 2, 'Xin cho biet ngay du kien cap cang?'),
(1, 4, 'Du kien cap cang Shanghai trong 3 ngay toi.'),
(3, 3, 'Hang bi giu o hai quan, can ho tro gap.');

-- ---- news ------------------------------------------------------------------
CREATE TABLE news (
    id           INT NOT NULL AUTO_INCREMENT,
    title        VARCHAR(200),
    body         TEXT,
    published_at DATETIME DEFAULT NOW(),
    PRIMARY KEY (id)
);

INSERT INTO news (title, body) VALUES
('Mo rong tuyen Shanghai - Rotterdam', 'IlFreight cong bo tuyen van tai moi...'),
('Nang cap he thong tra cuu van don',  'Cong cu tra cuu tracking duoc cai tien...');

-- ============================================================================
--  DATABASE: dev  (muc tieu enumeration lien-DB)
-- ============================================================================
CREATE DATABASE IF NOT EXISTS dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE dev;

-- ---- credentials (muc tieu dump) ------------------------------------------
CREATE TABLE credentials (
    id            INT NOT NULL AUTO_INCREMENT,
    username      VARCHAR(100),
    password_hash VARCHAR(64),
    api_key       VARCHAR(64),
    PRIMARY KEY (id)
);

-- password_hash = md5() cua mat khau that (de hoc vien crack neu muon)
INSERT INTO credentials (username, password_hash, api_key) VALUES
('dev_admin', '392037dbba51f692776d6cefb6dd546d', 'DEV-KEY-super-secret-0xC0FFEE'),
('backup_svc','9da2c9bcdf39d8610954e0e11ea8f45f', 'DEV-KEY-backup-4b1dp0nd');

-- ---- flags (co theo tung ky thuat — chung minh khai thac thanh cong) -------
CREATE TABLE flags (
    id        INT NOT NULL AUTO_INCREMENT,
    technique VARCHAR(60),
    flag      VARCHAR(120),
    PRIMARY KEY (id)
);

INSERT INTO flags (technique, flag) VALUES
('inband-union',   'ILF{un10n_b4s3d_dump_c0mpl3t3}'),
('inband-error',   'ILF{3rr0r_b4s3d_3xtr4ctv4lu3}'),
('blind-boolean',  'ILF{bl1nd_b00l34n_ch4r_by_ch4r}'),
('blind-time',     'ILF{t1m3_b4s3d_sl33p_5s}'),
('out-of-band',    'ILF{00b_3xf1l_v14_dns_ch4nn3l}'),
('stacked-query',  'ILF{st4ck3d_mult1_qu3ry_pwn3d}'),
('file-read',      'ILF{l04d_f1l3_r34d_3tc_p4sswd}'),
('file-write',     'ILF{1nt0_0utf1l3_w3bsh3ll_rc3}');

-- ============================================================================
--  Quay lai DB ung dung mac dinh
-- ============================================================================
USE ilfreight;
