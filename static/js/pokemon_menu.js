//Script de gestion d'onglet dans une page HTML

document.addEventListener("DOMContentLoaded", function () {
    // Récupérer les boutons et les menus
    var buttons = document.querySelectorAll(".button");
    var menus = document.querySelectorAll(".menu");

    menus[0].style.display = "block";
    
    // Associer un gestionnaire d'événements à chaque bouton
    buttons.forEach(function (button, index) {
        button.addEventListener("click", function () {
            // Cacher tous les menus
            menus.forEach(function (menu) {
                menu.style.display = "none";
            });

            // Afficher le menu correspondant au bouton cliqué
            menus[index].style.display = "block";
        });
    });
});
