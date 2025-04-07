from flask import Flask, render_template, request, redirect, url_for
import pymysql

app = Flask(__name__)

# Database connection function
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="8624910075",
        database="library_managemnet",
        cursorclass=pymysql.cursors.DictCursor
    )

# Home Page - Display Books
@app.route('/')
def index():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT book_id, title, availability_status, book_receiver_id, issue_date, return_date FROM Books")
        books = cursor.fetchall()
    conn.close()
    return render_template('index.html', books=books)

# Add a New Book
@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO Books (title, author, genre, availability_status, book_receiver_id, issue_date, return_date) 
                VALUES (%s, %s, %s, TRUE, NULL, NULL, NULL)
            """, (title, author, genre))
            conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add_book.html')

# Register User Info
@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        receiver_id = request.form['receiver_id']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO UserInfo (receiver_id, name, email)
                VALUES (%s, %s, %s)
            """, (receiver_id, name, email))
            conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('register.html')

# Select receiver to issue a book
@app.route('/select_receiver', methods=['GET', 'POST'])
def select_receiver():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT receiver_id, name FROM UserInfo")
        users = cursor.fetchall()
    conn.close()

    if request.method == 'POST':
        receiver_id = request.form['receiver_id']
        return redirect(url_for('choose_book', receiver_id=receiver_id))

    return render_template('select_receiver.html', users=users)

# Show available books to issue for selected receiver
@app.route('/choose_book/<receiver_id>', methods=['GET', 'POST'])
def choose_book(receiver_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM Books WHERE availability_status = TRUE")
        books = cursor.fetchall()
    conn.close()
    return render_template('choose_book.html', books=books, receiver_id=receiver_id)

# Issue a selected book
@app.route('/issue/<int:book_id>/<receiver_id>', methods=['POST'])
def issue_book(book_id, receiver_id):
    issue_date = request.form['issue_date']

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE Books 
            SET availability_status = FALSE, book_receiver_id = %s, issue_date = %s, return_date = NULL 
            WHERE book_id = %s
        """, (receiver_id, issue_date, book_id))

        cursor.execute("""
            INSERT INTO BookIssueHistory (book_id, receiver_id, issue_date, return_date, action_type, action_timestamp)
            VALUES (%s, %s, %s, NULL, 'issue', NOW())
        """, (book_id, receiver_id, issue_date))

        conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Return a Book
@app.route('/return/<int:book_id>', methods=['POST'])
def return_book(book_id):
    return_date = request.form['return_date']

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT book_receiver_id, issue_date FROM Books WHERE book_id = %s
        """, (book_id,))
        result = cursor.fetchone()

        cursor.execute("""
            UPDATE Books 
            SET availability_status = TRUE, book_receiver_id = NULL, issue_date = NULL, return_date = %s 
            WHERE book_id = %s
        """, (return_date, book_id))

        if result:
            cursor.execute("""
                INSERT INTO BookIssueHistory (book_id, receiver_id, issue_date, return_date, action_type, action_timestamp)
                VALUES (%s, %s, %s, %s, 'return', NOW())
            """, (book_id, result['book_receiver_id'], result['issue_date'], return_date))

        conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Delete a Book
@app.route('/delete/<int:book_id>')
def delete_book(book_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM Books WHERE book_id = %s", (book_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('index'))

# View all book issue/return records
@app.route('/history')
def view_history():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT h.history_id, b.title, h.receiver_id, h.issue_date, h.return_date, h.action_type, h.action_timestamp
            FROM BookIssueHistory h
            JOIN Books b ON h.book_id = b.book_id
            ORDER BY h.action_timestamp DESC
        """)
        history = cursor.fetchall()
    conn.close()
    return render_template('history.html', history=history)

if __name__ == '__main__':
    app.run(debug=True)