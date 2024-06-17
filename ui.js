function hpAnimation() {
    var enemyHpElement = document.querySelector(".hp-container .skills.enemy");
    var playerHpElement = document.querySelector(".hp-container .skills.player");

    // Function to update HP and width
    function updateHp() {
        var enemyHp = document.getElementById("enemyHp").querySelector('input[type="number"]').value;
        var playerHp = document.getElementById("playerHp").querySelector('input[type="number"]').value;
        var enemyHpPercentage = document.getElementById("enemyHpPercent").querySelector('input[type="number"]').value;
        var playerHpPercentage = document.getElementById("playerHpPercent").querySelector('input[type="number"]').value;

        enemyHpElement.textContent = enemyHp;
        playerHpElement.textContent = playerHp;
        enemyHpElement.style.width = enemyHpPercentage + "%";
        playerHpElement.style.width = playerHpPercentage + "%";
    }

    // Call updateHp initially
    updateHp();

    // Set interval for continuous updates
    var intervalId = setInterval(updateHp, 500); // 500 milliseconds = 0.5 seconds


    return 'Animation created';
}