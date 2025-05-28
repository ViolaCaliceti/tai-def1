import numpy as np
import random
import time
import os
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import copy

class MonteCarloAgent:
    def __init__(self, headless=False, simulations=1000):
        self.directions = ['up', 'right', 'down', 'left']
        self.key_mapping = {
            'up': Keys.ARROW_UP,
            'right': Keys.ARROW_RIGHT,
            'down': Keys.ARROW_DOWN,
            'left': Keys.ARROW_LEFT
        }
        self.headless = headless
        self.simulations = simulations  # Number of Monte Carlo simulations per move
        self.setup_browser()
        
    def setup_browser(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Add these options to fix common Chrome issues
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Use direct ChromeDriver path instead of webdriver_manager
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Get the absolute path to the HTML file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'index.html')
        self.driver.get(f"file://{file_path}")
        time.sleep(1)  # Wait for the page to load
        
    def get_grid_state(self):
        # Extract the grid state from the webpage
        grid_cells = self.driver.find_elements(By.CLASS_NAME, "grid")
        grid = np.zeros((4, 4), dtype=int)
        
        for i, cell in enumerate(grid_cells):
            row, col = i // 4, i % 4
            value_str = cell.get_attribute("data-value")
            if value_str and value_str.isdigit():
                grid[row][col] = int(value_str)
                
        return grid
    
    def get_score(self):
        score_element = self.driver.find_element(By.ID, "score")
        return int(score_element.text)
    
    def make_move(self, direction):
        # Make a move using the keyboard
        self.driver.find_element(By.TAG_NAME, "body").send_keys(self.key_mapping[direction])
        time.sleep(0.1)  # Small delay to allow animation
    
    def is_game_over(self):
        # Check if game over message is displayed
        try:
            message = self.driver.find_element(By.ID, "game-over-message")
            return message.is_displayed()
        except:
            # If we can't find the element, the game is not over
            return False
    
    def reset_game(self):
        # Check if game over message is displayed
        try:
            message_overlay = self.driver.find_element(By.ID, "game-over-message")
            if message_overlay.is_displayed():
                # If game over message is displayed, click the new game button in the message
                self.driver.find_element(By.ID, "new-game-message-button").click()
            else:
                # Otherwise click the regular new game button
                self.driver.find_element(By.ID, "new-game-button").click()
        except:
            # If any error occurs, try the regular new game button
            self.driver.find_element(By.ID, "new-game-button").click()
        
        time.sleep(0.5)  # Wait for the game to reset
    
    def move_grid(self, grid, direction):
        """Simulate a move on the grid and return the new grid, whether it changed, and the score gained"""
        grid_copy = grid.copy()
        score_gained = 0
        
        # Apply the move (simplified simulation)
        if direction == 'up':
            for j in range(4):
                for i in range(1, 4):
                    if grid_copy[i, j] != 0:
                        k = i
                        while k > 0 and (grid_copy[k-1, j] == 0 or grid_copy[k-1, j] == grid_copy[k, j]):
                            if grid_copy[k-1, j] == 0:
                                grid_copy[k-1, j] = grid_copy[k, j]
                                grid_copy[k, j] = 0
                                k -= 1
                            elif grid_copy[k-1, j] == grid_copy[k, j]:
                                grid_copy[k-1, j] *= 2
                                score_gained += grid_copy[k-1, j]
                                grid_copy[k, j] = 0
                                break
                            else:
                                break
        
        elif direction == 'down':
            for j in range(4):
                for i in range(2, -1, -1):
                    if grid_copy[i, j] != 0:
                        k = i
                        while k < 3 and (grid_copy[k+1, j] == 0 or grid_copy[k+1, j] == grid_copy[k, j]):
                            if grid_copy[k+1, j] == 0:
                                grid_copy[k+1, j] = grid_copy[k, j]
                                grid_copy[k, j] = 0
                                k += 1
                            elif grid_copy[k+1, j] == grid_copy[k, j]:
                                grid_copy[k+1, j] *= 2
                                score_gained += grid_copy[k+1, j]
                                grid_copy[k, j] = 0
                                break
                            else:
                                break
        
        elif direction == 'left':
            for i in range(4):
                for j in range(1, 4):
                    if grid_copy[i, j] != 0:
                        k = j
                        while k > 0 and (grid_copy[i, k-1] == 0 or grid_copy[i, k-1] == grid_copy[i, k]):
                            if grid_copy[i, k-1] == 0:
                                grid_copy[i, k-1] = grid_copy[i, k]
                                grid_copy[i, k] = 0
                                k -= 1
                            elif grid_copy[i, k-1] == grid_copy[i, k]:
                                grid_copy[i, k-1] *= 2
                                score_gained += grid_copy[i, k-1]
                                grid_copy[i, k] = 0
                                break
                            else:
                                break
        
        elif direction == 'right':
            for i in range(4):
                for j in range(2, -1, -1):
                    if grid_copy[i, j] != 0:
                        k = j
                        while k < 3 and (grid_copy[i, k+1] == 0 or grid_copy[i, k+1] == grid_copy[i, k]):
                            if grid_copy[i, k+1] == 0:
                                grid_copy[i, k+1] = grid_copy[i, k]
                                grid_copy[i, k] = 0
                                k += 1
                            elif grid_copy[i, k+1] == grid_copy[i, k]:
                                grid_copy[i, k+1] *= 2
                                score_gained += grid_copy[i, k+1]
                                grid_copy[i, k] = 0
                                break
                            else:
                                break
        
        # Check if the move changed the grid
        changed = not np.array_equal(grid, grid_copy)
        return grid_copy, changed, score_gained
    
    def get_empty_cells(self, grid):
        """Return a list of empty cell positions"""
        empty_cells = []
        for i in range(4):
            for j in range(4):
                if grid[i][j] == 0:
                    empty_cells.append((i, j))
        return empty_cells
    
    def add_random_tile(self, grid):
        """Add a random tile (2 or 4) to an empty cell"""
        empty_cells = self.get_empty_cells(grid)
        if not empty_cells:
            return grid
        
        # Choose a random empty cell
        i, j = random.choice(empty_cells)
        
        # 90% chance of adding a 2, 10% chance of adding a 4
        grid[i, j] = 2 if random.random() < 0.9 else 4
        
        return grid
    
    def is_game_over_grid(self, grid):
        """Check if the game is over (no valid moves)"""
        # If there are empty cells, the game is not over
        if np.any(grid == 0):
            return False
        
        # Check if there are any adjacent cells with the same value
        for i in range(4):
            for j in range(4):
                val = grid[i, j]
                # Check right and down neighbors
                for di, dj in [(0, 1), (1, 0)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < 4 and 0 <= nj < 4 and grid[ni, nj] == val:
                        return False
        
        return True
    
    def run_random_simulation(self, grid, initial_direction):
        """
        Run a random simulation from the given grid state, starting with the specified direction.
        Returns the final score achieved.
        """
        current_grid = grid.copy()
        total_score = 0
        
        # Make the initial move
        new_grid, changed, score = self.move_grid(current_grid, initial_direction)
        if not changed:
            return 0  # Invalid initial move
        
        current_grid = new_grid
        total_score += score
        
        # Add a random tile after the initial move
        current_grid = self.add_random_tile(current_grid)
        
        # Continue with random moves until game over
        while not self.is_game_over_grid(current_grid):
            # Choose a random direction
            directions = self.directions.copy()
            random.shuffle(directions)
            
            moved = False
            for direction in directions:
                new_grid, changed, score = self.move_grid(current_grid, direction)
                if changed:
                    current_grid = new_grid
                    total_score += score
                    moved = True
                    break
            
            if not moved:
                break  # No valid moves
            
            # Add a random tile
            current_grid = self.add_random_tile(current_grid)
        
        return total_score
    
    def simulate_batch(self, args):
        """Run a batch of simulations for a specific direction"""
        grid, direction, num_simulations = args
        if num_simulations <= 0:
            return direction, 0
            
        total_score = 0
        valid_simulations = 0
        
        for _ in range(num_simulations):
            score = self.run_random_simulation(grid, direction)
            if score > 0:  # Valid simulation
                total_score += score
                valid_simulations += 1
        
        avg_score = total_score / valid_simulations if valid_simulations > 0 else 0
        return direction, avg_score
    
    def get_best_move(self, grid):
        """
        Find the best move using Monte Carlo simulations.
        For each possible move, run multiple random simulations and choose the one with the highest average score.
        """
        # Check which moves are valid
        valid_moves = []
        for direction in self.directions:
            _, changed, _ = self.move_grid(grid, direction)
            if changed:
                valid_moves.append(direction)
        
        if not valid_moves:
            return random.choice(self.directions)  # No valid moves
        
        # If only one valid move, return it
        if len(valid_moves) == 1:
            return valid_moves[0]
        
        # Distribute simulations among valid moves
        simulations_per_move = self.simulations // len(valid_moves)
        
        # Prepare arguments for parallel processing
        args = [(grid, direction, simulations_per_move) for direction in valid_moves]
        
        # Run simulations in parallel using process pool
        results = []
        with ThreadPoolExecutor(max_workers=min(len(valid_moves), mp.cpu_count())) as executor:
            results = list(executor.map(self.simulate_batch, args))
        
        # Find the move with the highest average score
        best_move = max(results, key=lambda x: x[1])[0]
        
        # Debug information
        print("Move scores:")
        for direction, score in results:
            print(f"{direction}: {score:.2f}")
        
        return best_move
    
    def play_game(self, max_moves=5000):
        """Play a full game of 2048 using Monte Carlo simulations"""
        self.reset_game()
        move_count = 0
        
        # For tracking progress
        scores_history = []
        best_random_scores = []
        
        while move_count < max_moves and not self.is_game_over():
            grid = self.get_grid_state()
            current_score = self.get_score()
            scores_history.append(current_score)
            
            print(f"Move {move_count}, Current score: {current_score}")
            print(f"Highest tile: {np.max(grid)}")
            
            best_move = self.get_best_move(grid)
            
            # Store the best random score for visualization
            _, _, best_random_score = max([(d, *self.simulate_batch((grid, d, 10))) 
                                         for d in self.directions], key=lambda x: x[2])
            best_random_scores.append(best_random_score)
            
            print(f"Best move: {best_move}, Expected future score: {best_random_score:.2f}")
            
            self.make_move(best_move)
            move_count += 1
            
            # Optional: Add a small delay to visualize the game
            time.sleep(0.1)
        
        final_score = self.get_score()
        final_grid = self.get_grid_state()
        highest_tile = np.max(final_grid)
        
        print(f"Game over! Final score: {final_score}, Moves: {move_count}, Highest tile: {highest_tile}")
        
        # Save progress data for visualization
        progress_data = {
            "scores": scores_history,
            "best_random_scores": best_random_scores,
            "moves": list(range(len(scores_history)))
        }
        
        with open("monte_carlo_progress.json", "w") as f:
            json.dump(progress_data, f)
        
        return final_score, highest_tile, move_count
    
    def run_games(self, num_games=5):
        """Run multiple games and track statistics"""
        scores = []
        highest_tiles = []
        move_counts = []
        
        for game in range(num_games):
            print(f"Starting game {game+1}/{num_games}")
            score, highest_tile, move_count = self.play_game()
            scores.append(score)
            highest_tiles.append(int(highest_tile))
            move_counts.append(move_count)
        
        print(f"Games complete. Average score: {sum(scores)/len(scores)}")
        print(f"Best score: {max(scores)}")
        print(f"Highest tile reached: {max(highest_tiles)}")
        print(f"Average moves per game: {sum(move_counts)/len(move_counts)}")
        
        # Save results
        results = {
            "scores": scores,
            "highest_tiles": highest_tiles,
            "move_counts": move_counts,
            "average_score": sum(scores)/len(scores),
            "best_score": max(scores),
            "max_tile": max(highest_tiles),
            "average_moves": sum(move_counts)/len(move_counts)
        }
        
        with open("monte_carlo_results.json", "w") as f:
            json.dump(results, f)
    
    def close(self):
        """Close the browser"""
        self.driver.quit()

if __name__ == "__main__":
    # Create agent with 1000 simulations per move
    # Increase for better performance, decrease for faster execution
    agent = MonteCarloAgent(headless=False, simulations=1000)
    try:
        agent.run_games(num_games=3)
    finally:
        agent.close()