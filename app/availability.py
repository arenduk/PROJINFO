"""Disponibilite du materiel sur une plage de dates.

Un emprunt reserve `quantity` unites de `id_equipment` sur
[date_debut_prevue, date_retour_prevue]. La quantite disponible pour une
plage donnee = quantity_total - somme des `quantity` des emprunts en_attente
ou valide, non encore rendus, dont la plage chevauche celle demandee
(chevauchement : existing.debut <= new.fin AND new.debut <= existing.fin).
"""

from sqlalchemy import text

_OVERLAP_SQL = """
    SELECT COALESCE(SUM(quantity), 0) AS reserved
    FROM emprunt
    WHERE id_equipment = :id_equipment
      AND statut_validation IN ('en_attente', 'valide')
      AND date_retour_reelle IS NULL
      AND date_debut_prevue <= :date_fin
      AND date_retour_prevue >= :date_debut
      AND (:exclude_id IS NULL OR id_emprunt != :exclude_id)
"""


def get_available_quantity(
    session, id_equipment, date_debut, date_fin, exclude_emprunt_id=None, for_update=True
):
    """A utiliser sur les chemins d'ecriture (soumission, validation), dans la
    meme transaction que l'INSERT/UPDATE qui suit. `for_update=True` pose un
    verrou de ligne (SELECT ... FOR UPDATE) sur l'equipement pour serialiser
    deux soumissions/validations concurrentes sur le meme materiel : sans ca,
    deux personnes peuvent lire "3 disponibles" en meme temps et sur-reserver.

    Retourne None si l'equipement n'existe pas ou est desactive.
    """
    lock = " FOR UPDATE" if for_update else ""
    total = session.execute(
        text(f"SELECT quantity_total FROM equipment WHERE id_equipment = :id AND is_active = TRUE{lock}"),
        {"id": id_equipment},
    ).scalar()
    if total is None:
        return None
    reserved = session.execute(
        text(_OVERLAP_SQL),
        {
            "id_equipment": id_equipment,
            "date_debut": date_debut,
            "date_fin": date_fin,
            "exclude_id": exclude_emprunt_id,
        },
    ).scalar()
    return total - int(reserved or 0)


def list_availability(conn, date_debut, date_fin):
    """Lecture en masse pour la page de navigation du catalogue (une seule
    requete, pas de N+1). Ne montre que le materiel actif et en etat OK."""
    return conn.query(
        """
        SELECT e.id_equipment, e.name, e.category, e.description, e.etat, e.quantity_total,
               e.quantity_total - COALESCE((
                   SELECT SUM(em.quantity) FROM emprunt em
                   WHERE em.id_equipment = e.id_equipment
                     AND em.statut_validation IN ('en_attente', 'valide')
                     AND em.date_retour_reelle IS NULL
                     AND em.date_debut_prevue <= :date_fin
                     AND em.date_retour_prevue >= :date_debut
               ), 0) AS quantite_disponible
        FROM equipment e
        WHERE e.is_active = TRUE AND e.etat = 'OK'
        ORDER BY e.name
        """,
        params={"date_debut": date_debut, "date_fin": date_fin},
        ttl=10,
    )
