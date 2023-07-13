import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, END
from tkcalendar import DateEntry

class TodoApp:
    def __init__(self):
        self.conn = sqlite3.connect('todo.db')
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.current_user_id = None
        self.sort_by_deadline = False  
        self.root = tk.Tk()
        self.root.title("TODO App")

        self.create_login_screen()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                deadline DATE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        self.conn.commit()

    def create_login_screen(self):
        username_label = tk.Label(self.root, text="Username")
        username_label.grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        password_label = tk.Label(self.root, text="Password")
        password_label.grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        login_button = tk.Button(self.root, text="Login", command=self.login)
        login_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        register_button = tk.Button(self.root, text="Register", command=self.register)
        register_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        self.cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user_id = self.cursor.fetchone()

        if user_id:
            self.current_user_id = user_id[0]
            self.root.destroy()
            self.show_todo_screen()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username and password:
            try:
                self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                self.conn.commit()
                messagebox.showinfo("Registration", "Registration successful! Please log in.")
                self.clear_entries()
            except sqlite3.IntegrityError:
                messagebox.showerror("Registration Failed", "Username already exists.")
        else:
            messagebox.showerror("Registration Failed", "Username and password are required.")

    def show_todo_screen(self):
        todo_screen = tk.Tk()
        todo_screen.title("TODO App")

        title_label = tk.Label(todo_screen, text="Title")
        title_label.grid(row=0, column=0, padx=5, pady=5)
        self.title_entry = tk.Entry(todo_screen)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)

        description_label = tk.Label(todo_screen, text="Description")
        description_label.grid(row=1, column=0, padx=5, pady=5)
        self.description_entry = tk.Entry(todo_screen)
        self.description_entry.grid(row=1, column=1, padx=5, pady=5)

        deadline_label = tk.Label(todo_screen, text="Deadline")
        deadline_label.grid(row=2, column=0, padx=5, pady=5)
        self.deadline_entry = DateEntry(todo_screen, date_pattern='yyyy-mm-dd')
        self.deadline_entry.grid(row=2, column=1, padx=5, pady=5)

        add_button = tk.Button(todo_screen, text="Add Task", command=self.add_todo)
        add_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        sort_button = tk.Button(todo_screen, text="Toggle Sort by Deadline", command=self.toggle_sort_by_deadline)
        sort_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        self.treeview = ttk.Treeview(todo_screen, columns=("Title", "Description", "Deadline"), show="headings")
        self.treeview.heading("Title", text="Title")
        self.treeview.heading("Description", text="Description")
        self.treeview.heading("Deadline", text="Deadline")
        self.treeview.column("Title", width=200)
        self.treeview.column("Description", width=200)
        self.treeview.column("Deadline", width=100)
        self.treeview.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        #self.treeview.bind("<<TreeviewSelect>>", self.on_todo_select)
        self.treeview.bind("<<TreeviewSelect>>")

        delete_button = tk.Button(todo_screen, text="Delete Task", command=self.delete_todo)
        delete_button.grid(row=6, column=0, columnspan=2, padx=5, pady=5)

        self.update_todo_list()

        todo_screen.mainloop()

    def add_todo(self):
        title = self.title_entry.get()
        description = self.description_entry.get()
        deadline = self.deadline_entry.get()

        if title and deadline:
            self.cursor.execute("SELECT title FROM todos WHERE title=?", (title,))
            if self.cursor.fetchone():
                messagebox.showerror("Identical title", "Title identical,  make another")
                return

            try:
                self.cursor.execute("INSERT INTO todos (user_id, title, description, deadline) VALUES (?, ?, ?, ?)",
                                    (self.current_user_id, title, description, deadline))
                self.conn.commit()
                self.update_todo_list()
                self.title_entry.delete(0, END)
                self.description_entry.delete(0, END)
                self.deadline_entry.delete(0, END)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showerror("Add Todo", "Title and deadlin e are required.")

    def delete_todo(self):
        selected_items = self.treeview.selection()

        for item in selected_items:
            todo_id = self.treeview.item(item)["values"][0]
            self.cursor.execute("DELETE FROM todos WHERE title=?", (todo_id,))
            self.conn.commit()

        self.update_todo_list()

    def update_todo_list(self):
        self.treeview.delete(*self.treeview.get_children())
        if self.sort_by_deadline:
            self.cursor.execute("SELECT id, title, description, deadline FROM todos WHERE user_id=? ORDER BY deadline ASC",
                                (self.current_user_id,))
        else:
            self.cursor.execute("SELECT id, title, description, deadline FROM todos WHERE user_id=?",
                                (self.current_user_id,))
        todos = self.cursor.fetchall()

        for todo in todos:
            self.treeview.insert("", "end", values=(todo[1], todo[2], todo[3]))

    def toggle_sort_by_deadline(self):
        self.sort_by_deadline = not self.sort_by_deadline
        self.update_todo_list()

    def clear_entries(self):
        self.username_entry.delete(0, END)
        self.password_entry.delete(0, END)

    def on_todo_select(self, event):
        selected_item = self.treeview.selection()

        if selected_item:
            todo_id = self.treeview.item(selected_item)["values"][0]
            self.show_todo_details(todo_id)

    def show_todo_details(self, todo_id):
        if hasattr(self, "details_window"):
            self.details_window.destroy()

        self.details_window = tk.Toplevel()
        self.details_window.title("Todo Details")

        self.cursor.execute("SELECT title, description, deadline FROM todos WHERE id=?", (todo_id,))
        todo = self.treeview.item(self.treeview.focus())["values"]
        

        if todo:
            title_label = tk.Label(self.details_window, text="Title:")
            title_label.grid(row=0, column=0, padx=5, pady=5)
            title_value = tk.Label(self.details_window, text=todo[0])
            title_value.grid(row=0, column=1, padx=5, pady=5)

            description_label = tk.Label(self.details_window, text="Description:")
            description_label.grid(row=1, column=0, padx=5, pady=5)
            description_value = tk.Label(self.details_window, text=todo[1])
            description_value.grid(row=1, column=1, padx=5, pady=5)

            deadline_label = tk.Label(self.details_window, text="Deadline:")
            deadline_label.grid(row=2, column=0, padx=5, pady=5)
            deadline_value = tk.Label(self.details_window, text=todo[2])
            deadline_value.grid(row=2, column=1, padx=5, pady=5)

    def run(self):
        self.root.mainloop()

    def close(self):
        self.conn.close()

app = TodoApp()
app.run()
app.close()
