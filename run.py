from app import create_app

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Product': Product, 'Category': Category, 'Review': Review}


if __name__ == "__main__":
    app.run(debug=True)