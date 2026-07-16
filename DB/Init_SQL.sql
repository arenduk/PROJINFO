create database if not exists SAP_bis;

use SAP_bis;

CREATE TABLE user (
id_user INT primary key AUTO_INCREMENT,
last_name VARCHAR(100),
first_name VARCHAR(100),
email VARCHAR(255),
user_status VARCHAR(20)
);

create table equipment(
id_equipment int primary key AUTO_INCREMENT,
name varchar(100),
description varchar(255),
category varchar(100),
disponibility BOOLEAN NOT NULL DEFAULT TRUE,  
etat varchar(20),
CONSTRAINT chk_etat CHECK (etat IN ('OK', 'NOK', 'perdu'))
);

create table emprunt(
id_emprunt int primary key AUTO_INCREMENT,
date_emprunt DATETIME,
date_retour_prevue DATETIME,
date_retour_reelle DATETIME NULL, # NULL signifie que le matériel n est pas encore rendu
statut_validation varchar(20),
CONSTRAINT chk_statut_validation CHECK (statut_validation IN ('en_attente', 'valide', 'non_valide')),
id_user int,
id_equipment int,
CONSTRAINT fk_id_user
FOREIGN KEY (id_user) REFERENCES user(id_user),
CONSTRAINT fk_id_equipment
FOREIGN KEY (id_equipment) REFERENCES equipment(id_equipment)
);

-- ET GLOBAL event_scheduler = ON;

INSERT INTO user ( last_name, first_name, email, user_status)
VALUES
('Fritsch', 'Antoine', 'antoine.fritsh@2028.icam.fr', 'admin'),
('Poupin', 'Gabriel', 'gabriel.poupin@2028.icam.fr', 'user'),
('Pham', 'Lucas', 'lucas.pham@2028.icam.fr', 'admin'),
('Guyon', 'Max', 'max.guyon@2028.icam.fr', 'admin'),
('Heimlich', 'Vincent', 'vincent.heimlich@2028.icam.fr', 'user'),
('Lecointe', 'Liman', 'liman.lecointe@2028.icam.fr', 'user');

/* insert into user (last_name, first_name, email, user_status)
 * values
 * (vlast_name, vfirst_name, vemail, user); #vlast_name = variable last_name dans le code etc...
 * */

INSERT INTO equipment (name, description, category, disponibility, etat)
VALUES
('Tablette', 'Ipad 11 pro', 'Informatique', TRUE, 'OK'),
('Kit Raspberry PI 5', 'Kit Raspberry PI 5 avec ecran, clavier, souris, picam', 'Informatique', TRUE, 'OK'),
('Routeur Cisco C1300', 'Routeur Cisco C1300', 'Informatique', FALSE, 'OK'),
('ESP', 'ESP32 avec puce wifi', 'electronique', FALSE, 'perdu'),
('LEDs', 'LEDs de differentes couleurs', 'electronique', TRUE, 'OK'),
('Capteurs de temperature', 'Capteur de temperature', 'electronique', TRUE, 'OK'),
('Capteurs d\'humidite', 'Capteur d\'humidite', 'electronique', TRUE, 'OK'),
('Photodetecteurs', 'Photodetecteur de lumière', 'electronique', TRUE, 'OK'),
('Acceleromètres', 'Module acceleromètre', 'electronique', TRUE, 'OK'),
('Capteurs de proximite', 'Capteur de proximite de presence', 'electronique', TRUE, 'OK'),
('Indicateurs de pression', 'Capteur / Indicateur de pression', 'electronique', TRUE, 'OK'),
('Capteurs de niveau', 'Capteur de niveau de liquide', 'electronique', TRUE, 'OK'),
('Kit RFID, RC Lecteur, Puce et Carte', 'Kit RFID complet avec lecteur et cartes', 'electronique', TRUE, 'OK'),
('Lecteurs code à barre', 'Lecteur de code-barres USB', 'Informatique', TRUE, 'OK'),
('Resistances', 'Lot de resistances variees', 'electronique', TRUE, 'OK'),
('Boutons poussoirs', 'Bouton poussoir de prototypage', 'electronique', TRUE, 'OK'),
('Arduino', 'Carte microcontrôleur Arduino', 'electronique', TRUE, 'OK'),
('Connecteurs', 'Lot de connecteurs', 'electronique', TRUE, 'OK'),
('Câbles Breadboard', 'Câbles de prototypage (Jumper wires)', 'electronique', TRUE, 'OK'),
('Câbles alimentation', 'Câble d\'alimentation', 'electronique', TRUE, 'OK'),
('Petits Moteurs', 'Petit moteur CC', 'electronique', TRUE, 'OK'),
('Servo moteurs', 'Servo moteur de modelisme', 'electronique', TRUE, 'OK'),
('Breadboards', 'Plaque d\'essai pour prototypage', 'electronique', TRUE, 'OK'),
('Potentiomètres', 'Potentiomètre rotatif', 'electronique', TRUE, 'OK'),
('ecrans LCD', 'Module ecran LCD', 'electronique', TRUE, 'OK'),
('Transistors', 'Lot de transistors', 'electronique', TRUE, 'OK'),
('Condensateurs', 'Lot de condensateurs', 'electronique', TRUE, 'OK')
;
/*
 * INSERT INTO equipment (name, description, category, equipment_status, etat)
VALUES
(vname, vdescription, vcategory, vequip_status, vetat)
 * */


insert into emprunt(date_emprunt, date_retour_prevue, date_retour_reelle, id_user, id_equipment)
values
('2026-03-25','2026-06-11','2026-06-14', 3, 7),
('2026-01-30','2026-06-12',NULL, 4, 1)
;
insert into emprunt(date_emprunt, date_retour_prevue, id_user, id_equipment)
values
('2026-03-25','2026-06-16', 2, 6);

Create view v_retard as 
select id_emprunt, id_user,id_equipment, date_retour_prevue,
datediff(now(), date_retour_prevue) as jours_de_retard
from emprunt
where now() > date_retour_prevue and date_retour_reelle is NULL;