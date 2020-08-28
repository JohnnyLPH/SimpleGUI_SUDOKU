# Create a Sudoku app with GUI, can be used to solve Sudoku or create random Sudoku to play.
import math
import numpy
import tkinter
import time
import threading
import random
import os
import sys


class Sudoku:  # Sudoku Class.
    def __init__(self, size):
        self.total_row = int(size)  # Classic Sudoku size = 9 rows * 9 columns.
        
        self.block_row = int(math.sqrt(self.total_row))  # Number of block rows / columns = square root of total rows.

        self.empty_row = list(0 for _ in range(self.total_row))  # 0 represents empty.

        self.grid = []  # Grid of the Sudoku.

        for _ in range(self.total_row):
            self.grid.append(self.empty_row)

        self.grid = numpy.array(self.grid)

        self.empty_grid = self.grid.copy()
        
        self.empty_spots = []  # Store spots that are empty.

        for row in range(self.total_row):
            for col in range(self.total_row):
                self.empty_spots.append(list([row, col]))

        # For later use.
        self.got_result = None
        self.overall_start_time = None
        self.all_results = None
        self.solve_start_time = None
        self.current_result = None
        self.non_empty_spots = None

    def reset_empty(self):
        self.grid = self.empty_grid.copy()
        
        self.empty_spots = []

        for row in range(self.total_row):
            for col in range(self.total_row):
                self.empty_spots.append(list([row, col]))
        return

    def __repr__(self):
        return f"<Sudoku {self.total_row} x {self.total_row}>"

    @staticmethod
    def find_next_empty(grid, rows_order, cols_order):  # Find next empty.
        for row in rows_order:
            for col in cols_order:
                if grid[row][col] == 0:
                    return row, col

        return None  # None, solved Sudoku.

    @staticmethod
    def valid_option(grid, c_row, c_col, c_option, total_row, block_row):  # Checked if current option is valid or not.
        # IMPORTANT:
        #   Instead of always referring to self.total_row and self.block_row in the function, passing them as arguments
        #   of the function in the very beginning can save a lot of time and speed up the function.
        if c_option not in grid[c_row]:  # Check whole row [Left to Right].
            for row in range(total_row):  # Check whole column [Top to Bottom].
                if c_option == grid[row][c_col]:
                    return False

            # Check the block.
            block_start_row = (c_row // block_row) * block_row
            block_start_col = (c_col // block_row) * block_row

            for row in range(block_start_row, block_start_row + block_row):  # Loop through block rows.
                for col in range(block_start_col, block_start_col + block_row):  # Loop through block columns.
                    if grid[row][col] == c_option:
                        return False
            return True  # Option can be used.
        else:
            return False
    
    def solve_sudoku(self, grid, total_row, block_row, rows_order, cols_order):  # Solve Sudoku using backtracking.
        # IMPORTANT:
        #   Instead of always referring to self.total_row & self.block_row in child function, passing them as arguments
        #   of the parent function in the very beginning can save a lot of time and speed up the function.
        next_empty = Sudoku.find_next_empty(grid, rows_order, cols_order)
        
        if next_empty is None or self.got_result is True:  # Solved the Sudoku.
            if self.got_result is False:  # First result.
                self.all_results.append(grid)  # Add to results list.
                self.got_result = True
            return True
        
        if time.perf_counter() - self.solve_start_time > block_row * 2:  # Maximum time allowed per solving attempt.
            return False

        options = [num + 1 for num in range(total_row)]
        
        random.shuffle(options)

        for option in options:
            if Sudoku.valid_option(grid, next_empty[0], next_empty[1], option, total_row, block_row) is True:
                grid[next_empty[0]][next_empty[1]] = option
                
                if self.solve_sudoku(grid, total_row, block_row, rows_order, cols_order) is True:
                    return True

                grid[next_empty[0]][next_empty[1]] = 0
        return False

    def solve_with_threads(self):  # Solve the Sudoku by using multiple threads to get one solution.
        self.overall_start_time = time.perf_counter()
        self.got_result = False

        self.all_results = []

        total_row = self.total_row
        block_row = self.block_row

        # Arrange rows to search in ascending order based on number of empty spots in each row.
        rows_order = {}

        # Arrange columns to search in ascending order based on number of empty spots in each column.
        cols_order = {}

        for row in range(total_row):
            for col in range(total_row):
                if self.grid[row][col] == 0:  # Counting empty spots.
                    rows_order[row] = rows_order.get(row, 0) + 1
                    cols_order[col] = cols_order.get(col, 0) + 1

        # Rearrange based on number of empty spots.
        rows_order = sorted(rows_order.items(), key=lambda item: item[1])
        cols_order = sorted(cols_order.items(), key=lambda item: item[1])
        
        # Final lists created.
        rows_order = [item[0] for item in rows_order]
        cols_order = [item[0] for item in cols_order]

        while time.perf_counter() - self.overall_start_time < block_row * total_row * 2:  # Maximum overall time.
            self.solve_start_time = time.perf_counter()

            threads = []  # Store all threads created.

            for _ in range(total_row * block_row * 4):  # Number of threads used in each cycle.
                thread = threading.Thread(
                    target=self.solve_sudoku, args=(self.grid.copy().tolist(), total_row, block_row,
                                                    rows_order, cols_order)
                    )  # After testing, normal list is found to be a faster choice so change to normal list for solving.
                thread.start()
                threads.append(thread)

            for t in threads:
                t.join()  # Wait for all threads to finish running before proceeding.

            if len(self.all_results) == 0:  # No result, continue cycle.
                continue
            else:
                break
        
        if len(self.all_results) == 0:
            return False  # Didn't solve in time.
        else:
            self.grid = random.choice(numpy.array(self.all_results))  # Change back to numpy array after solving.
            return True

    def create_sudoku_puzzle(self):  # Function to create a random puzzle.
        # Solve to make sure it has a result first before creating the puzzle.
        if self.solve_with_threads() is False:
            return False  # No result is available for creating a puzzle.

        self.current_result = self.grid.copy()  # For reference as a solution of the puzzle that will be created.

        self.non_empty_spots = []  # Store spots that are not empty.
        
        self.empty_spots = []  # Store empty spots.

        for row in range(self.total_row):
            for col in range(self.total_row):
                self.non_empty_spots.append(list([row, col]))

        random.shuffle(self.non_empty_spots)

        for _ in range(random.randint(55, 65)):  # Maximum numbers to remove is 65, minimum is 55.
            spot = random.choice(self.non_empty_spots)

            self.grid[spot[0]][spot[-1]] = 0  # Empty the spot.
            
            self.non_empty_spots.remove(spot)  # Remove the spot from non-empty spots list.
            
            self.empty_spots.append(spot)  # Add the spot to empty spots list.
        return True  # Puzzle is created.
        

class GUI:  # GUI Class.
    def __init__(self):
        self.sudoku = Sudoku(9)  # Create Sudoku.
        
        self.window = tkinter.Tk()
    
        # Store all colors and fonts here for easy access.
        self.window_color = "#B8F9E2"
        
        self.frame_color = "#5CEAB9"
        
        self.button_color = "#21EC75"
        self.button_color2 = "#82F4B1"
        self.button_color3 = "#FFFFFF"
        self.button_color4 = "#FEF376"

        self.start_b_color = "#11FA04"
        self.reset_b_color = "#FB0606"

        font_family = ["Times", "Helvetica", "Verdana", "Courier"]

        self.frame_font = (font_family[0], 20, 'bold')
        self.label_font = (font_family[1], 14)
        self.button_font = (font_family[2], 10, 'bold')
        self.info_font = (font_family[3], 10)

        self.window.title("Sudoku By JohnnyLPH")
        self.window.configure(bg=self.window_color)

        # Main Menu.
        self.info_frame1 = tkinter.LabelFrame(self.window, text="Main Menu", bg=self.frame_color,
                                              font=self.frame_font)
        self.info_frame1.grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="news")

        # Info Panel.
        self.info_frame2 = tkinter.LabelFrame(self.window, text="Info Panel", bg=self.frame_color,
                                              font=self.frame_font)
        self.info_frame2.grid(row=1, column=1, rowspan=9, padx=(5, 10), pady=(5, 10), sticky="news")
        
        # Sudoku Board.
        self.game_frame = tkinter.LabelFrame(self.window, text="Sudoku Board", bg=self.frame_color,
                                             font=self.frame_font)
        self.game_frame.grid(row=0, column=0, rowspan=10, padx=(10, 5), pady=10)

        # For later use.
        self.mode = None
        self.blocks_list = None
        self.info_list = None
        self.solution_button = None
        self.select_buttons = None
        self.empty_buttons = None
        self.valid_records_list = None
        self.ori_num_list = None
        self.first_spot = None
        self.changed_spots = None
        self.win_value = None
        self.valid_spots_count = None
        self.invalid_spots_count = None
        self.solved_sudoku = None
        self.mark_ending = None

        self.show_mode()  # Show Main Menu.
        self.show_grid()  # Show Sudoku Board.
        self.show_info()  # Show Info Panel.

        self.window.update_idletasks()
        
        win_width = self.window.winfo_reqwidth()
        win_height = self.window.winfo_reqheight()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x_coord = int(screen_width / 2 - win_width / 2)
        y_coord = int(screen_height / 2 - win_height / 2)

        self.window.geometry(f"+{x_coord}+{y_coord}")  # Center the window on the screen.
        self.window.resizable(0, 0)  # Not resizeable.
        self.window.mainloop()  # Mainloop.

    def show_mode(self):
        label_1 = tkinter.Label(self.info_frame1, text="Choose Mode", bg=self.frame_color, font=self.label_font)
        
        self.mode = 1  # 1 for Play Sudoku; 2 for Solve Sudoku.

        def choose_mode(mode):
            if mode == 2:
                button_1.configure(command=lambda: choose_mode(1), bg=self.button_color2, relief="raised")
                button_2.configure(bg=self.button_color, relief="sunken")
            else:
                button_1.configure(bg=self.button_color, relief="sunken")
                button_2.configure(command=lambda: choose_mode(2), bg=self.button_color2, relief="raised")

            self.mode = mode

            button_1.grid(row=1, column=0, sticky="n", padx=(5, 1), pady=5)
            button_2.grid(row=1, column=1, sticky="n", padx=(1, 5), pady=5)
            return
        
        button_1 = tkinter.Button(self.info_frame1, text="Play Sudoku")
        button_1.configure(bg=self.button_color, activebackground=self.button_color, font=self.button_font,
                           relief="sunken")

        button_2 = tkinter.Button(self.info_frame1, text="Solve Sudoku", command=lambda: choose_mode(2))
        button_2.configure(activebackground=self.button_color, font=self.button_font, bg=self.button_color2)

        def reset_program():  # Re-execute the whole script.
            os.execl(sys.executable, sys.executable, *sys.argv)

        def start_mode():  # Start running main stuffs.
            label_1.configure(state="disabled")
            button_1.configure(state="disabled")
            button_2.configure(state="disabled")

            label_1.grid(row=0, column=0, columnspan=2, sticky="n")
            button_1.grid(row=1, column=0, sticky="n", padx=(5, 1), pady=5)
            button_2.grid(row=1, column=1, sticky="n", padx=(1, 5), pady=5)
            
            start_reset_button.configure(text="Reset", command=reset_program)
            start_reset_button.configure(activebackground=self.start_b_color, bg=self.reset_b_color, fg="white")
            start_reset_button.grid(row=2, column=0, columnspan=2, padx=5, pady=(5, 0), sticky="we")

            if self.mode == 1:
                self.play_sudoku()  # Show non-empty spots first.
            else:
                self.update_empty_spots()  # Straight display empty spots.

        start_reset_button = tkinter.Button(self.info_frame1, text="Start", font=self.button_font, command=start_mode)
        start_reset_button.configure(activebackground=self.reset_b_color, bg=self.start_b_color)

        label_1.grid(row=0, column=0, columnspan=2, sticky="n")

        button_1.grid(row=1, column=0, sticky="n", padx=(5, 1), pady=5)
        button_2.grid(row=1, column=1, sticky="n", padx=(1, 5), pady=5)

        start_reset_button.grid(row=2, column=0, columnspan=2, padx=5, pady=(5, 0), sticky="we")
        return
    
    def show_grid(self):
        self.blocks_list = []  # Needed for later use since the Sudoku is divided into 9 different blocks for display.

        for block_row in range(self.sudoku.block_row):
            for block_col in range(self.sudoku.block_row):
                block = tkinter.LabelFrame(self.game_frame, bg=self.button_color)
                
                block.grid(row=block_row, column=block_col, sticky="news")
                
                self.blocks_list.append(block)

                # Structure inside each block is built by displaying labels first which will set the shape of the block.
                for row in range(self.sudoku.block_row):
                    for col in range(self.sudoku.block_row):
                        display_spot = tkinter.Label(block, font=self.button_font, width=5, height=3,
                                                     bg=self.button_color3)
                        display_spot.grid(row=row, column=col, padx=1, pady=1, sticky="news")
        return
    
    def show_info(self):
        self.info_list = []

        text = "# Choose one mode and click\nStart Button."

        info1 = tkinter.Label(self.info_frame2, text=text, font=self.info_font, bg=self.frame_color)
        info1.grid(row=0, column=0, sticky="n", padx=1, pady=1)

        self.info_list.append(info1)  # Will be destroyed later.
        return

    def get_block(self, c_row, c_col):  # Used to get the block which current spot resides in.
        if c_row in [0, 1, 2]:  # Block in row 1.
            if c_col in [0, 1, 2]:  # Block in column 1.
                return self.blocks_list[0], (0, 0)
            elif c_col in [3, 4, 5]:  # Block in column 2.
                return self.blocks_list[1], (0, 3)
            else:  # Block in column 3.
                return self.blocks_list[2], (0, 6)
        elif c_row in [3, 4, 5]:  # Block in row 2.
            if c_col in [0, 1, 2]:  # Block in column 1.
                return self.blocks_list[3], (3, 0)
            elif c_col in [3, 4, 5]:  # Block in column 2.
                return self.blocks_list[4], (3, 3)
            else:  # Block in column 3.
                return self.blocks_list[5], (3, 6)
        else:  # Block in row 3.
            if c_col in [0, 1, 2]:  # Block in column 1.
                return self.blocks_list[6], (6, 0)
            elif c_col in [3, 4, 5]:  # Block in column 2.
                return self.blocks_list[7], (6, 3)
            else:  # Block in column 3.
                return self.blocks_list[8], (6, 6)
    
    def show_solution(self, first_call=True):  # Show solution of the Sudoku.
        def get_solution():
            if self.mode == 2 and self.invalid_spots_count != 0:  # At least one invalid spots that are not empty.
                return
            
            self.solved_sudoku = True  # Set it True to disable all empty spots while finding a solution.
            
            self.solution_button.configure(state="disabled")  # Disable solution button while finding a solution.
            
            self.solution_button.grid(row=3, column=0, columnspan=2, padx=5, pady=(10, 0), sticky="we")
            
            if self.mode == 1:  # Play Mode, already has a solution.
                self.sudoku.grid = self.sudoku.current_result

                self.mark_ending = True  # Mark as the end of program since there's a solution.
            else:  # Solve Mode.
                if self.sudoku.solve_with_threads() is True:  # Has a solution.
                    self.mark_ending = True  # Mark as the end of program since there's a solution.

            self.finish_sudoku()  # Show the final info.
            return
        
        if first_call is True:  # First call, create solution button.
            self.solution_button = tkinter.Button(self.info_frame1, font=self.button_font)
            self.solution_button.configure(activebackground=self.reset_b_color, bg=self.start_b_color,
                                           command=get_solution)
            
            if self.mode == 1:  # Show.
                self.solution_button.configure(text="Show Solution")
            else:  # Find.
                self.solution_button.configure(text="Find Solution")
            
            self.solution_button.grid(row=3, column=0, columnspan=2, padx=5, pady=(10, 0), sticky="we")
        else:  # Not first call.
            if self.changed_spots is False:  # First click on an empty spot, disable solution button.
                self.solution_button.configure(state="disabled")
            else:  # Only available after changing spots or assigning value.
                self.solution_button.configure(state="normal")

            self.solution_button.grid(row=3, column=0, columnspan=2, padx=5, pady=(10, 0), sticky="we")
        return
    
    def finish_sudoku(self):  # Show final info to end the program.
        for row in range(self.sudoku.block_row):
            for col in range(self.sudoku.block_row):
                self.select_buttons[row][col].destroy()  # Destroy all select buttons.

        for info in self.info_list:
            info.destroy()  # Destroy all current info.
        
        self.window.update_idletasks()

        if self.solved_sudoku is True:  # First condition. Should always be True if this function is called.
            end1 = tkinter.Label(self.info_frame2, font=self.info_font, bg=self.frame_color)
            
            if self.mark_ending is True:  # Second condition. There's definitely a solution.
                end1.configure(text="# Sudoku is solved!")

                if self.valid_spots_count == self.win_value:  # Solved by player.
                    self.solution_button.configure(state="disabled")  # Disable solution button.

                    self.solution_button.grid(row=3, column=0, columnspan=2, padx=5, pady=(10, 0), sticky="we")
                else:  # Solved by computer.
                    thread1 = threading.Thread(target=self.update_empty_spots, args=(False,))  # Display the solution.

                    thread1.start()
            else:  # No solution available.
                end1.configure(text="# Sudoku cannot be solved!")

            end1.grid(row=0, column=0, sticky="news", padx=1, pady=1)

            end2 = tkinter.Label(self.info_frame2, font=self.info_font, bg=self.frame_color)
            end2.configure(text="# Click Reset Button to\nrestart or close window to\nterminate program.")

            end2.grid(row=1, column=0, sticky="news", padx=1, pady=1)

            if self.mark_ending is False:  # No solution. Create extra button to try again.
                def try_again():
                    end1.destroy()
                    end2.destroy()
                    end3.destroy()

                    self.window.update_idletasks()

                    self.solved_sudoku = False  # Set to False so now all empty spots are available again.
                    
                    thread2 = threading.Thread(target=self.assign_value)  # Display old info again.
                    thread3 = threading.Thread(target=self.show_solution, args=(False,))  # Enable the solution button.

                    thread2.start()
                    thread3.start()
                    return
                
                end3 = tkinter.Button(self.info_frame2,  bg=self.button_color2, activebackground=self.button_color)
                end3.configure(text="Try Again", font=self.button_font)
                end3.configure(command=try_again)
                end3.grid(row=2, column=0, padx=5, pady=5, sticky="n")
        return
    
    def assign_value(self, first_call=True):  # Assign value to spot and display info.
        def make_value_change(value):
            self.changed_spots = True  # Equivalent to changing spots.
            
            if self.sudoku.grid[self.first_spot[0]][self.first_spot[-1]] != value:  # Only if different values.
                self.sudoku.grid[self.first_spot[0]][self.first_spot[-1]] = value  # Assign value to the spot.
            
            thread1 = threading.Thread(target=self.update_empty_spots, args=(False,))
            thread2 = threading.Thread(target=self.assign_value, args=(False,))
            thread3 = threading.Thread(target=self.show_solution, args=(False,))

            thread1.start()
            thread2.start()
            thread3.start()
            return
        
        def control_select_buttons(b_row, b_col, state):  # Easier to disable and enable select buttons.
            c_select_button = self.select_buttons[b_row][b_col]
            c_select_button.configure(state=state)
            c_select_button.grid(row=b_row, column=b_col, padx=1, pady=1, sticky="news")

        if self.changed_spots is False or first_call is True:  # First click or first call.
            if first_call is True:  # First call, display all info needed.
                if len(self.info_list) == 1:  # Only if it's the very first call.
                    self.info_list[0].destroy()  # Destroy before displaying other info.
                
                self.info_list = []
                
                first_info = tkinter.Label(self.info_frame2, font=self.info_font, bg=self.frame_color)
                first_info.configure(text="# Double-click: Empty Spot")
                first_info.grid(row=0, column=0, sticky="n", padx=1, pady=1)

                self.info_list.append(first_info)

                text = "# Select Two: Switch Spots"
                second_info = tkinter.Label(self.info_frame2, text=text, font=self.info_font, bg=self.frame_color)
                second_info.grid(row=1, column=0, sticky="n", padx=1, pady=1)
                
                self.info_list.append(second_info)

                text2 = "# Assign Value:"
                select_value_label = tkinter.Label(self.info_frame2, text=text2, font=self.info_font,
                                                   bg=self.frame_color)
                select_value_label.grid(row=2, column=0, sticky="n", padx=1, pady=1)

                self.info_list.append(select_value_label)

                inner_select_frame = tkinter.LabelFrame(self.info_frame2, bg=self.button_color)  # Select buttons frame.
                inner_select_frame.grid(row=3, column=0, sticky="n", padx=(2, 0), pady=1)

                self.info_list.append(inner_select_frame)

                value_list = [num + 1 for num in range(self.sudoku.total_row)]  # Values that can be assigned.
                
                self.select_buttons = []

                value_index = -1
                
                for row in range(self.sudoku.block_row):
                    row_buttons = []
                    
                    for col in range(self.sudoku.block_row):
                        value_index += 1
                        
                        select_button = tkinter.Button(inner_select_frame, width=5, height=3, bg=self.button_color3)
                        
                        select_button.configure(activebackground=self.button_color4, relief='flat')
                        select_button.configure(text=value_list[value_index], font=self.button_font, state="disabled")
                        select_button.configure(command=lambda value=value_list[value_index]: make_value_change(value))
                        
                        select_button.grid(row=row, column=col, padx=1, pady=1, sticky="news")

                        row_buttons.append(select_button)
                    
                    self.select_buttons.append(row_buttons)
            else:  # First click. Make value selection be available.
                for row in range(self.sudoku.block_row):
                    for col in range(self.sudoku.block_row):
                        thread = threading.Thread(target=control_select_buttons, args=(row, col, "normal"))

                        thread.start()
        else:  # Second click or after assigning value.
            for row in range(self.sudoku.block_row):
                for col in range(self.sudoku.block_row):
                    thread = threading.Thread(target=control_select_buttons, args=(row, col, "disabled"))

                    thread.start()
        return

    def update_empty_spots(self, first_call=True):  # Display and update empty spots as buttons.
        if first_call is True:  # First call, create all things needed for later use.
            self.empty_buttons = {}  # Store empty spot buttons.
            
            self.valid_records_list = {}  # Keep track of which spot is valid and which is not.
            
            self.ori_num_list = {}  # Keep track of the values of spots.
            
            self.first_spot = None  # Store position of first spot for assigning value.

            # Used while resetting values of first spot and second spot or assigning value to first spot.
            self.changed_spots = False
            
            self.win_value = len(self.sudoku.empty_spots)  # Used to determine if the Sudoku is solved by player.

            self.valid_spots_count = 0  # Count number of valid spots and used to compare with self.win_value.
            self.invalid_spots_count = 0  # Count number of invalid spots that are not empty.

            self.solved_sudoku = False  # True if all spots are valid or the computer is searching for a solution.

            self.mark_ending = False  # Mark the end of program. Click reset button to re-execute the whole script.

        def update_each_empty(empty):  # Update value of spot.
            # Solved the Sudoku or still searching for solution, make all buttons useless now.
            if self.solved_sudoku is True:
                return
            
            if self.changed_spots is True:  # Changed spots pr assigned a value, empty stored position.
                self.first_spot = None
                self.changed_spots = False
            
            if self.first_spot is None:  # First click.
                self.first_spot = empty  # Store first spot.

                # Reset both counts.
                self.valid_spots_count = 0
                self.invalid_spots_count = 0
            else:  # Second click.
                row, col = empty[0], empty[-1]  # Position of second spot.
                second_num = self.sudoku.grid[row][col]  # Value of second spot.

                if empty == self.first_spot:  # Double-click on same spot. Empty the spot.
                    self.sudoku.grid[row][col] = 0
                else:  # Exchange values.
                    # Only if different values.
                    if self.sudoku.grid[self.first_spot[0]][self.first_spot[-1]] != second_num:
                        # Change second spot.
                        self.sudoku.grid[row][col] = self.sudoku.grid[self.first_spot[0]][self.first_spot[-1]]
                        
                        self.sudoku.grid[self.first_spot[0]][self.first_spot[-1]] = second_num  # Change first spot.
                
                self.changed_spots = True  # Mark the changing of spots.
            
            thread_1 = threading.Thread(target=self.update_empty_spots, args=(False,))
            thread_2 = threading.Thread(target=self.assign_value, args=(False,))
            thread_3 = threading.Thread(target=self.show_solution, args=(False,))

            thread_1.start()
            thread_2.start()
            thread_3.start()
            return
        
        def show_each_empty(empty):  # Display spots.
            empty_spot_index = self.sudoku.empty_spots.index(empty)
            
            row, col = empty[0], empty[-1]

            block = self.get_block(row, col)
            
            if self.sudoku.grid[row][col] == 0:
                text = ""  # Display nothing.
            else:
                text = self.sudoku.grid[row][col]

            if first_call is True:  # First call. Create all empty spot buttons.
                button = tkinter.Button(block[0], text=text, font=self.label_font)
                
                button.configure(relief="flat", command=lambda e_empty=empty: update_each_empty(e_empty))
                button.configure(activebackground=self.button_color4, bg=self.button_color3)
                
                button.grid(row=row - block[1][0], column=col - block[1][-1], padx=1, pady=1, sticky="news")

                self.empty_buttons[empty_spot_index] = button  # Store the button.
                
                self.valid_records_list[empty_spot_index] = False  # Record spot as invalid.
                
                self.ori_num_list[empty_spot_index] = 0 if text == "" else text  # Record value of spot.
            else:  # Not first call, check each spot to see if it's valid or not.
                button = self.empty_buttons[empty_spot_index]  # Get the button of current spot.
                
                if self.first_spot is not None and self.changed_spots is False:  # First click, assigning value.
                    if self.first_spot == empty:  # It's the current spot.
                        button.configure(bg=self.button_color4, activebackground=self.button_color3)
                        
                        button.grid(row=row - block[1][0], column=col - block[1][-1], padx=1, pady=1, sticky="news")
                        return
                    else:  # Not current spot, end function here.
                        return
                else:  # Not assigning value. First spot must be displayed again no matter the condition.
                    if text == "":  # Current spot is empty.
                        # Not first spot and same value.
                        if empty != self.first_spot and self.ori_num_list[empty_spot_index] == 0:
                            return  # No change is needed since it is already empty before.

                        button.configure(text=text, fg="black", activebackground=self.button_color4,
                                         bg=self.button_color3)
                        
                        button.grid(row=row - block[1][0], column=col - block[1][-1], padx=1, pady=1, sticky="news")

                        self.ori_num_list[empty_spot_index] = 0  # New value = 0.
                        
                        self.valid_records_list[empty_spot_index] = False  # 0 is invalid.
                        # Return here since the Sudoku is definitely not solved yet.
                        return
                    else:  # Not empty, there's a chance that the Sudoku is solved.
                        backup_grid = self.sudoku.grid.copy()  # Backup for checking valid spot.
                        backup_grid[row][col] = 0  # Empty current spot before checking.

                        # Valid spot.
                        if self.sudoku.valid_option(backup_grid, row, col, text, self.sudoku.total_row,
                                                    self.sudoku.block_row) is True:
                            self.valid_spots_count += 1  # Add valid spots count.

                            # Valid and same value as before.
                            if self.valid_records_list[empty_spot_index] is True and \
                                    self.ori_num_list[empty_spot_index] == text:
                                if empty == self.first_spot:  # It's the first spot, need to make change to the button.
                                    button.configure(text=text, fg="black", activebackground=self.button_color4,
                                                     bg=self.button_color3)
                                
                                    button.grid(row=row - block[1][0], column=col - block[1][-1], padx=1, pady=1,
                                                sticky="news")
                            else:  # Change from invalid to valid.
                                self.valid_records_list[empty_spot_index] = True  # Valid now.
                                
                                button.configure(text=text, fg="black", activebackground=self.button_color4,
                                                 bg=self.button_color3)
                                
                                button.grid(row=row - block[1][0], column=col - block[1][-1], padx=1, pady=1,
                                            sticky="news")
                        else:  # Invalid spot, change foreground to red color.
                            self.invalid_spots_count += 1  # Add invalid spots count.
                            
                            # Invalid and same value as before.
                            if self.valid_records_list[empty_spot_index] is False and \
                                    self.ori_num_list[empty_spot_index] == text:
                                if empty == self.first_spot:  # It's the first spot, need to make change to the button.
                                    button.configure(text=text, fg="red", activebackground=self.button_color4,
                                                     bg=self.button_color3)
                                    
                                    button.grid(row=row - block[1][0], column=col - block[1][-1], padx=1, pady=1,
                                                sticky="news")
                            else:  # Change from valid to invalid.
                                self.valid_records_list[empty_spot_index] = False  # Invalid now.
                                
                                button.configure(text=text, fg="red", activebackground=self.button_color4,
                                                 bg=self.button_color3)
                                
                                button.grid(row=row - block[1][0], column=col - block[1][-1], padx=1, pady=1,
                                            sticky="news")

                        self.ori_num_list[empty_spot_index] = text  # New value is recorded.

                # Sudoku is solved by player.
                if self.win_value == self.valid_spots_count and self.invalid_spots_count == 0:
                    if self.mark_ending is False:
                        self.solved_sudoku = True
                        
                        self.mark_ending = True

                        self.finish_sudoku()  # Display final info.
            return
        
        for spot in self.sudoku.empty_spots:  # Loop through all empty spots.
            thread = threading.Thread(target=show_each_empty, args=(list(spot),))
            thread.start()

        if first_call is True:  # First call. Prepare info. Display solution button.
            thread2 = threading.Thread(target=self.assign_value)
            thread3 = threading.Thread(target=self.show_solution)

            thread2.start()
            thread3.start()
        return
    
    def play_sudoku(self):  # Play mode selected, display non-empty spots.
        if self.sudoku.create_sudoku_puzzle() is True:
            # Display non-empty spots first in the game frame.
            def show_each_non_empty(non_empty):
                row, col = non_empty[0], non_empty[-1]
                
                block = self.get_block(row, col)
                
                label = tkinter.Label(block[0], text=self.sudoku.grid[row][col], font=self.label_font)
                
                label.configure(bg=self.window_color)  # Color is different from empty spots.
                
                label.grid(row=row - block[1][0], column=col - block[1][-1], padx=1, pady=1, sticky="news")
                return
            
            for spot in self.sudoku.non_empty_spots:
                thread = threading.Thread(target=show_each_non_empty, args=(list(spot),))
                thread.start()
            
            self.update_empty_spots()  # Display empty spots.
            return True
        else:
            return False  # No puzzle is created.


start_gui = GUI()
# Completed. Date: 13/8/2020 1:13 PM
