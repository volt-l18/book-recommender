from flask import Flask, render_template, request
import pickle
import pandas as pd
import difflib

app = Flask(__name__)

# Load preprocessed data
books = pickle.load(open("books.pkl", "rb"))
popular = pickle.load(open("popular.pkl", "rb"))
pt = pickle.load(open("pt.pkl", "rb"))
similarity_scores = pickle.load(open("similarity_scores.pkl", "rb"))

@app.route('/')
def index():
    # Displays the Top 50 books from popular.pkl
    return render_template(
        "index.html",
        book_name=list(popular["Book-Title"].values),
        author=list(popular["Book-Author"].values),
        image=list(popular["Image-URL-M"].values),
        votes=list(popular["num_ratings"].values),
        ratings=list(popular["avg_rating"].values)
    )

@app.route('/recommend')
def recommend_page():
    # Shows the recommendation form (empty by default)
    return render_template("recommend.html", user_input="")

@app.route('/recommend_books', methods=['POST'])
def recommend_books():
    # Store the raw user input so we can display it exactly as typed
    user_input_raw = request.form.get("book_name", "")
    # For matching logic, use a stripped and lowercased version
    user_input = user_input_raw.strip().lower()
    
    # Normalize the pivot table index by stripping and converting to lowercase
    pt_index_lower = [str(title).strip().lower() for title in pt.index]

    # Try to find partial matches first (substring match)
    partial_matches = [title for title in pt_index_lower if user_input in title]
    if partial_matches:
        # Use the first partial match
        matched_input = partial_matches[0]
    else:
        # Fallback to fuzzy matching if no partial match is found
        closest_matches = difflib.get_close_matches(user_input, pt_index_lower, n=1, cutoff=0.6)
        if closest_matches:
            matched_input = closest_matches[0]
        else:
            # Pass the user_input_raw back so it remains in the search box
            return render_template("recommend.html", error="Book not found. Please try another title.", user_input=user_input_raw)

    # Get the actual index of the matching book
    index_loc = pt_index_lower.index(matched_input)

    # Sort books by similarity score (descending), ignoring the book itself
    similar_books = sorted(
        list(enumerate(similarity_scores[index_loc])),
        key=lambda x: x[1],
        reverse=True
    )[1:5]

    recommendations = []
    for i in similar_books:
        # Retrieve the actual title from pt.index and normalize it
        matched_title = str(pt.index[i[0]]).strip()
        # Retrieve the book details using case-insensitive and stripped comparison
        details = books[books['Book-Title'].str.lower().str.strip() == matched_title.lower()].iloc[0]
        recommendations.append((
            details['Book-Title'],
            details['Book-Author'],
            details['Image-URL-M']
        ))
    
    # Pass user_input_raw so the text remains in the search box
    return render_template("recommend.html", recommendations=recommendations, user_input=user_input_raw)

if __name__ == "__main__":
    app.run(debug=True)
