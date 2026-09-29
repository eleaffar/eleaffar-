// Configurazione del negozio: incolla qui i link di checkout di Lemon Squeezy
// (Store > Products > Share > "Checkout link"). Finché sono vuoti, i pulsanti
// mostrano "Disponibile a breve".
window.SHOP = {
  gestionaleForfettario: ""
};
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-product]").forEach(function (el) {
    var url = window.SHOP[el.dataset.product];
    if (url) { el.href = url; } else { el.textContent = "Disponibile a breve"; el.removeAttribute("href"); el.classList.add("secondary"); }
  });
});
