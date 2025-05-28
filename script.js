document.addEventListener('DOMContentLoaded', () => {
    let grid = Array(4).fill().map(() => Array(4).fill(0));
    let score = 0;

    // Initialize game
    function initGame() {
        grid = Array(4).fill().map(() => Array(4).fill(0));
        score = 0;
        addNewNumber();
        addNewNumber();
        updateDisplay();
    }

    // Add new number (2 or 4) to random empty cell
    function addNewNumber() {
        let emptyCells = [];
        for (let i = 0; i < 4; i++) {
            for (let j = 0; j < 4; j++) {
                if (grid[i][j] === 0) {
                    emptyCells.push({x: i, y: j});
                }
            }
        }
        if (emptyCells.length > 0) {
            const randomCell = emptyCells[Math.floor(Math.random() * emptyCells.length)];
            // Modificato: ora il 4 ha probabilità del 20%
            grid[randomCell.x][randomCell.y] = Math.random() < 0.8 ? 2 : 4;
        }
    }

    // Animate tile
    function animateTile(cell, isNew = false, isMerged = false) {
        if (isNew) {
            cell.classList.add('pop');
            setTimeout(() => cell.classList.remove('pop'), 150);
        }
        if (isMerged) {
            cell.classList.add('merge');
            setTimeout(() => cell.classList.remove('merge'), 200);
        }
    }
    
    // Update display
    function updateDisplay() {
        const gridCells = document.querySelectorAll('.grid');
        let cellIndex = 0;
        for (let i = 0; i < 4; i++) {
            for (let j = 0; j < 4; j++) {
                const value = grid[i][j];
                const cell = gridCells[cellIndex];
                const oldValue = cell.getAttribute('data-value');
                
                cell.setAttribute('data-value', value || '');
                cell.className = `grid ${value ? 'tile-' + value : ''}`;
                
                if (value && !oldValue) {
                    animateTile(cell, true, false);
                } else if (value && oldValue && value > oldValue) {
                    animateTile(cell, false, true);
                }
                
                cellIndex++;
            }
        }
        document.getElementById('score').textContent = score;
    }

    // Funzione helper per spostare e fondere una riga/colonna
    function moveAndMergeArray(arr) {
        // Array per tracciare quali celle sono già state fuse
        let merged = new Array(4).fill(false);
        let moved = false;
        
        // Prima, spostiamo tutti i numeri verso l'inizio dell'array
        let newArr = arr.filter(val => val !== 0);
        
        // Poi, fondiamo i numeri adiacenti uguali (solo una volta per cella)
        for (let i = 0; i < newArr.length - 1; i++) {
            if (newArr[i] === newArr[i + 1] && !merged[i] && !merged[i + 1]) {
                newArr[i] *= 2;
                score += newArr[i];
                newArr.splice(i + 1, 1); // Rimuovi l'elemento fuso
                merged[i] = true;
                moved = true;
            }
        }
        
        // Riempi con zeri fino a raggiungere la lunghezza 4
        while (newArr.length < 4) {
            newArr.push(0);
        }
        
        // Controlla se l'array è cambiato
        for (let i = 0; i < 4; i++) {
            if (arr[i] !== newArr[i]) {
                moved = true;
                break;
            }
        }
        
        return { arr: newArr, moved: moved };
    }

    // Handle moves - versione ottimizzata e corretta
    function move(direction) {
        let moved = false;
        const oldGrid = JSON.parse(JSON.stringify(grid));

        switch(direction) {
            case 'up':
                for (let j = 0; j < 4; j++) {
                    // Estrai la colonna
                    let column = [];
                    for (let i = 0; i < 4; i++) {
                        column.push(grid[i][j]);
                    }
                    
                    // Muovi e fondi
                    let result = moveAndMergeArray(column);
                    if (result.moved) moved = true;
                    
                    // Rimetti la colonna nella griglia
                    for (let i = 0; i < 4; i++) {
                        grid[i][j] = result.arr[i];
                    }
                }
                break;
                
            case 'down':
                for (let j = 0; j < 4; j++) {
                    // Estrai la colonna e invertila
                    let column = [];
                    for (let i = 3; i >= 0; i--) {
                        column.push(grid[i][j]);
                    }
                    
                    // Muovi e fondi
                    let result = moveAndMergeArray(column);
                    if (result.moved) moved = true;
                    
                    // Rimetti la colonna nella griglia (re-invertendo)
                    for (let i = 0; i < 4; i++) {
                        grid[3 - i][j] = result.arr[i];
                    }
                }
                break;
                
            case 'left':
                for (let i = 0; i < 4; i++) {
                    // La riga è già nell'ordine corretto
                    let result = moveAndMergeArray([...grid[i]]);
                    if (result.moved) moved = true;
                    grid[i] = result.arr;
                }
                break;
                
            case 'right':
                for (let i = 0; i < 4; i++) {
                    // Inverti la riga
                    let row = [...grid[i]].reverse();
                    
                    // Muovi e fondi
                    let result = moveAndMergeArray(row);
                    if (result.moved) moved = true;
                    
                    // Rimetti la riga nella griglia (re-invertendo)
                    grid[i] = result.arr.reverse();
                }
                break;
        }

        if (moved) {
            addNewNumber();
            updateDisplay();
            checkWinOrGameOver();
        }
    }

    // Check if game is over
    function isGameOver() {
        // Controlla se ci sono celle vuote
        for (let i = 0; i < 4; i++) {
            for (let j = 0; j < 4; j++) {
                if (grid[i][j] === 0) return false;
            }
        }
        
        // Controlla se ci sono mosse possibili (tessere adiacenti uguali)
        for (let i = 0; i < 4; i++) {
            for (let j = 0; j < 4; j++) {
                // Controlla a destra
                if (j < 3 && grid[i][j] === grid[i][j + 1]) return false;
                // Controlla in basso
                if (i < 3 && grid[i][j] === grid[i + 1][j]) return false;
            }
        }
        
        return true;
    }

    function checkWinOrGameOver() {
        // Check for 2048 tile
        let has2048 = false;
        let gameOver = isGameOver();
        
        for (let i = 0; i < 4; i++) {
            for (let j = 0; j < 4; j++) {
                if (grid[i][j] === 2048) {
                    has2048 = true;
                    break;
                }
            }
        }

        const messageOverlay = document.getElementById('game-over-message');
        const messageText = document.getElementById('message-text');
        const newGameButton = document.getElementById('new-game-message-button');

        if (has2048 && !window.gameWon) {
            window.gameWon = true;
            messageText.textContent = "You've reached 2048! Continue playing?";
            messageOverlay.style.display = 'flex';
            newGameButton.textContent = 'Continue';
            newGameButton.onclick = function() {
                messageOverlay.style.display = 'none';
            };
        } else if (gameOver) {
            messageText.textContent = "Game Over! No more moves available.";
            messageOverlay.style.display = 'flex';
            newGameButton.textContent = 'New Game';
            newGameButton.onclick = function() {
                window.gameWon = false;
                initGame();
                messageOverlay.style.display = 'none';
            };
        }
    }

    // Event listeners
    document.addEventListener('keydown', (e) => {
        switch(e.key) {
            case 'ArrowUp': 
                e.preventDefault(); // Previene lo scroll della pagina
                move('up'); 
                break;
            case 'ArrowDown': 
                e.preventDefault();
                move('down'); 
                break;
            case 'ArrowLeft': 
                e.preventDefault();
                move('left'); 
                break;
            case 'ArrowRight': 
                e.preventDefault();
                move('right'); 
                break;
        }
    });

    // Button controls
    document.getElementById('move-up').addEventListener('click', () => move('up'));
    document.getElementById('move-down').addEventListener('click', () => move('down'));
    document.getElementById('move-left').addEventListener('click', () => move('left'));
    document.getElementById('move-right').addEventListener('click', () => move('right'));

    // New game buttons
    document.getElementById('new-game-button').addEventListener('click', () => {
        window.gameWon = false;
        initGame();
    });

    // Start game
    initGame();
});