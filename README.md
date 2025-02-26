![image](https://github.com/user-attachments/assets/df514f14-5755-44ef-a77b-1d2e0643c4a6)

## This is for Session 11: databases

### Useful links: 
* [Flask Templates](https://flask.palletsprojects.com/en/stable/tutorial/templates/#)
* [Template Designer](https://jinja.palletsprojects.com/en/stable/templates/)
* [Bootstrap Forms](https://getbootstrap.com/docs/5.3/forms/overview/#overview)

### A working version can be found here:
* [https://hultagram.fly.dev/](https://hultagram.fly.dev/)

### Forking and cloning repositories into your own account
* [https://docs.github.com/en/desktop/adding-and-cloning-repositories/cloning-and-forking-repositories-from-github-desktop
](https://docs.github.com/en/desktop/adding-and-cloning-repositories/cloning-and-forking-repositories-from-github-desktop)

1. **Clone the repository**
   ```sh
   git clone https://github.com/yourusername/hultagram.git
   cd hultagram
   ```

2. **If working locally: Create and activate a virtual environment (optional but recommended)**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```sh
   python app.py
   ```
   The application will start on `http://127.0.0.1:5000/`

5. **Test functionality**
   - Create several posts with different images
   - Add comments to posts
   - Like posts to verify functionality

## Database

- The SQLite database (`photogram.db`) is created automatically when the app is first run.
- It stores posts, comments, and likes.

## Contributing

Feel free to fork the repository and submit pull requests with improvements!

## License

This project is licensed under the MIT License.
