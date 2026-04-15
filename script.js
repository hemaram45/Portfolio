window.addEventListener("scroll", () => {
    document.querySelectorAll(".card").forEach(card => {
        card.style.opacity = "1";
        card.style.transform = "translateY(0)";
    });
});