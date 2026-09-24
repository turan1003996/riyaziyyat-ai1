@app.route('/question/<int:q_id>', methods=['GET', 'POST'])
def question_detail(q_id):
    question = Question.query.get_or_404(q_id)

    if request.method == 'POST':
        # Əgər istifadəçi giriş etməyibsə, rəy yazmağa icazə vermir!
        if not current_user.is_authenticated:
            flash("Cavab/Rəy yazmaq üçün daxil olmalısınız!", "warning")
            return redirect(url_for('login'))

        content = request.form.get('content', '').strip()
        # ... (fayl yükləmə və baza əməliyyatları)