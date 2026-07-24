-- IcamTrack - schema complet
-- Gestion d'emprunt de materiel : demande -> validation par un gestionnaire -> retour.

CREATE DATABASE IF NOT EXISTS SAP_bis
    DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE SAP_bis;

-- ---------------------------------------------------------------------------
-- Utilisateurs
-- role : 'user' (emprunteur standard) < 'stock_manager' (valide les emprunts,
-- gere le catalogue) < 'admin' (en plus : roles, journal d'activite, parametres
-- du site). Un role superieur herite des droits des roles inferieurs.
-- ---------------------------------------------------------------------------
CREATE TABLE user (
    id_user       INT PRIMARY KEY AUTO_INCREMENT,
    email         VARCHAR(255) NOT NULL,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'user',
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME     NULL,
    CONSTRAINT uq_user_email UNIQUE (email),
    CONSTRAINT chk_user_role CHECK (role IN ('user', 'stock_manager', 'admin'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Catalogue de materiel.
-- quantity_total remplace l'ancien booleen "disponibility" : un booleen n'a
-- aucun sens pour du consommable en vrac (resistances, cables...), une
-- quantite si. La quantite reellement disponible a une date donnee se calcule
-- a la volee (voir app/availability.py), elle n'est jamais stockee ici.
-- ---------------------------------------------------------------------------
CREATE TABLE equipment (
    id_equipment   INT PRIMARY KEY AUTO_INCREMENT,
    name           VARCHAR(100) NOT NULL,
    description    VARCHAR(255),
    category       VARCHAR(100),
    quantity_total INT          NOT NULL DEFAULT 1,
    etat           VARCHAR(20)  NOT NULL DEFAULT 'OK',
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_equipment_etat CHECK (etat IN ('OK', 'NOK', 'perdu')),
    CONSTRAINT chk_equipment_quantity CHECK (quantity_total >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Emprunts (demandes de reservation de materiel sur une plage de dates).
-- date_demande  : horodatage de la soumission (auto).
-- date_debut_prevue / date_retour_prevue : plage souhaitee par l'emprunteur.
-- date_retour_reelle : NULL tant que le materiel n'est pas physiquement rendu.
-- statut_validation : en_attente -> valide|refuse (par un gestionnaire),
--                     ou annule (par l'emprunteur lui-meme, tant qu'en_attente).
-- ---------------------------------------------------------------------------
CREATE TABLE emprunt (
    id_emprunt             INT PRIMARY KEY AUTO_INCREMENT,
    id_user                INT NOT NULL,
    id_equipment           INT NOT NULL,
    quantity               INT NOT NULL DEFAULT 1,
    date_demande           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_debut_prevue      DATE NOT NULL,
    date_retour_prevue     DATE NOT NULL,
    date_retour_reelle     DATETIME NULL,
    statut_validation      VARCHAR(20) NOT NULL DEFAULT 'en_attente',
    commentaire_validation VARCHAR(255) NULL,
    id_validateur          INT NULL,
    date_validation        DATETIME NULL,
    CONSTRAINT fk_emprunt_user       FOREIGN KEY (id_user) REFERENCES user(id_user),
    CONSTRAINT fk_emprunt_equipment  FOREIGN KEY (id_equipment) REFERENCES equipment(id_equipment),
    CONSTRAINT fk_emprunt_validateur FOREIGN KEY (id_validateur) REFERENCES user(id_user),
    CONSTRAINT chk_emprunt_statut    CHECK (statut_validation IN ('en_attente', 'valide', 'refuse', 'annule')),
    CONSTRAINT chk_emprunt_quantity  CHECK (quantity > 0),
    CONSTRAINT chk_emprunt_dates     CHECK (date_retour_prevue >= date_debut_prevue),
    INDEX idx_emprunt_equipment_statut (id_equipment, statut_validation, date_retour_reelle),
    INDEX idx_emprunt_user (id_user)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Notifications utilisateur (cloche du bandeau).
-- ---------------------------------------------------------------------------
CREATE TABLE notification (
    id_notification INT PRIMARY KEY AUTO_INCREMENT,
    id_user         INT NOT NULL,
    type            VARCHAR(30) NOT NULL,
    message         VARCHAR(255) NOT NULL,
    id_emprunt      INT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notification_user    FOREIGN KEY (id_user) REFERENCES user(id_user),
    CONSTRAINT fk_notification_emprunt FOREIGN KEY (id_emprunt) REFERENCES emprunt(id_emprunt),
    INDEX idx_notification_user_read (id_user, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Journal d'activite (page Administration - "voir les logs").
-- ---------------------------------------------------------------------------
CREATE TABLE journal_audit (
    id_journal INT PRIMARY KEY AUTO_INCREMENT,
    id_user    INT NULL,
    action     VARCHAR(50) NOT NULL,
    details    TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_journal_user FOREIGN KEY (id_user) REFERENCES user(id_user),
    INDEX idx_journal_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Parametres du site (page Administration, cle/valeur).
-- ---------------------------------------------------------------------------
CREATE TABLE site_settings (
    setting_key   VARCHAR(50) PRIMARY KEY,
    setting_value VARCHAR(500),
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO site_settings (setting_key, setting_value) VALUES
    ('site_name', 'IcamTrack'),
    ('contact_email', 'contact@icam.fr'),
    ('maintenance_mode', 'false'),
    ('maintenance_message', '');

-- ---------------------------------------------------------------------------
-- Vue des emprunts en retard.
-- Fix vs l'ancienne version : celle-ci n'excluait pas les demandes refusees /
-- en attente (sans date_retour_reelle par definition), qui remontaient donc
-- a tort comme "en retard". On ne considere en retard qu'un emprunt valide,
-- non rendu, dont la date de retour prevue est depassee.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_retard AS
SELECT id_emprunt, id_user, id_equipment, quantity, date_debut_prevue, date_retour_prevue,
       DATEDIFF(CURDATE(), date_retour_prevue) AS jours_de_retard
FROM emprunt
WHERE statut_validation = 'valide'
  AND date_retour_reelle IS NULL
  AND date_retour_prevue < CURDATE();

-- ---------------------------------------------------------------------------
-- Donnees de demarrage : uniquement le catalogue de materiel.
-- Pas de seed sur `user` / `emprunt` / `notification` : les comptes sont
-- crees automatiquement a la premiere connexion Google de chacun (voir
-- app/auth.py - le tout premier compte cree devient admin).
-- ---------------------------------------------------------------------------
INSERT INTO equipment (name, description, category, quantity_total, etat) VALUES
('Tablette', 'iPad 11 Pro', 'Informatique', 2, 'OK'),
('Kit Raspberry Pi 5', 'Kit Raspberry Pi 5 avec ecran, clavier, souris, PiCam', 'Informatique', 3, 'OK'),
('Routeur Cisco C1300', 'Routeur Cisco C1300', 'Informatique', 1, 'OK'),
('ESP32', 'ESP32 avec puce wifi', 'Electronique', 0, 'perdu'),
('LEDs', 'LEDs de differentes couleurs', 'Electronique', 200, 'OK'),
('Capteurs de temperature', 'Capteur de temperature', 'Electronique', 15, 'OK'),
('Capteurs d''humidite', 'Capteur d''humidite', 'Electronique', 15, 'OK'),
('Photodetecteurs', 'Photodetecteur de lumiere', 'Electronique', 10, 'OK'),
('Accelerometres', 'Module accelerometre', 'Electronique', 10, 'OK'),
('Capteurs de proximite', 'Capteur de proximite de presence', 'Electronique', 10, 'OK'),
('Indicateurs de pression', 'Capteur / indicateur de pression', 'Electronique', 8, 'OK'),
('Capteurs de niveau', 'Capteur de niveau de liquide', 'Electronique', 8, 'OK'),
('Kit RFID', 'Kit RFID complet avec lecteur, puce et cartes', 'Electronique', 5, 'OK'),
('Lecteurs code a barre', 'Lecteur de code-barres USB', 'Informatique', 4, 'OK'),
('Resistances', 'Lot de resistances variees', 'Electronique', 500, 'OK'),
('Boutons poussoirs', 'Bouton poussoir de prototypage', 'Electronique', 100, 'OK'),
('Arduino', 'Carte microcontroleur Arduino', 'Electronique', 20, 'OK'),
('Connecteurs', 'Lot de connecteurs', 'Electronique', 300, 'OK'),
('Cables breadboard', 'Cables de prototypage (jumper wires)', 'Electronique', 150, 'OK'),
('Cables alimentation', 'Cable d''alimentation', 'Electronique', 30, 'OK'),
('Petits moteurs', 'Petit moteur CC', 'Electronique', 20, 'OK'),
('Servo moteurs', 'Servo moteur de modelisme', 'Electronique', 15, 'OK'),
('Breadboards', 'Plaque d''essai pour prototypage', 'Electronique', 40, 'OK'),
('Potentiometres', 'Potentiometre rotatif', 'Electronique', 60, 'OK'),
('Ecrans LCD', 'Module ecran LCD', 'Electronique', 12, 'OK'),
('Transistors', 'Lot de transistors', 'Electronique', 200, 'OK'),
('Condensateurs', 'Lot de condensateurs', 'Electronique', 300, 'OK');
