import json
from flask import Flask, request, jsonify
from flask_cors import CORS

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    CORS(app)
    setup_db(app)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/categories', methods=['GET'])
    def retrieve_categories():
        """
        Fetches all existent categories
        ---
        tags:
          - categories
        responses:
          200:
            success: Boolean indicating operation status
            categories: Dictionary containing category entries
        """
        categories = Category.query.order_by(Category.type).all()

        return jsonify({
            'success': True,
            'categories':
                {category.id: category.type for category in categories}
        })

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def retrieve_questions_by_category(category_id):
        """
        Query questions searching for text fragments within question body
        ---
        tags:
          - category
        responses:
          200:
            success: Boolean indicating operation status
            questions: Array of questions
          500:
            success: Boolean indicating operation status
            error: Unknown error
        """
        try:
            questions = \
                Question.query.filter(Question.category == category_id).all()
            return jsonify({
                'success': True,
                'questions': [question.format() for question in questions]
            })
        except Exception as e:
            print(e)
            return json.dumps({
                'success': False,
                'error': "An error occurred"
            }), 500


    @app.route('/questions', methods=['GET'])
    def retrieve_questions():
        """
        Fetches question paginating results
        ---
        tags:
          - questions
        responses:
          200:
            success: Boolean indicating operation status
            categories: Dictionary containing category entries
        """
        items_limit = request.args.get('limit', 10, type=int)
        selected_page = request.args.get('page', 1, type=int)
        current_index = selected_page - 1
        question_count = Question.query.count()
        questions = \
            Question.query.order_by(
                Question.id
            ).limit(items_limit).offset(current_index * items_limit).all()
        # honestly, I don't like the approach of fetching all categories again,
        # but following the requirement here.
        categories = Category.query.order_by(Category.type).all()

        return jsonify({
            'success': True,
            'categories':
                {category.id: category.type for category in categories},
            'questions': [question.format() for question in questions],
            'total_questions': question_count,
            'selected_page': selected_page
        })

    @app.route('/questions/<question_id>', methods=['DELETE'])
    def delete_question(question_id):
        """
        Delete a question with a given ID
        ---
        tags:
          - questions
        responses:
          200:
            success: Boolean indicating operation status
            deleted_id: deleted Question ID
          404:
            success: Boolean indicating operation status
            error: Error reason
        """
        question = \
            Question.query.filter(Question.id == question_id).one_or_none()
        if question:
            question.delete()
            return jsonify({
                'success': True,
                'deleted_id': question_id
            })
        else:
            return json.dumps({
                'success': False,
                'error': 'Drink #' + question_id + ' not found to be deleted'
            }), 404

    @app.route('/questions', methods=['POST'])
    def create_question():
        """
        Create a new question
        ---
        tags:
          - questions
        responses:
          201:
            success: Boolean indicating operation status
            question_id: created Question ID
          400:
            success: Boolean indicating operation status
            error: Invalid params
          500:
            success: Boolean indicating operation status
            error: Unknown error
        """
        data = dict(request.form or request.json or request.data)
        new_question = Question(
            question=data.get('question'),
            answer=data.get('answer'),
            category=data.get('category'),
            difficulty=data.get('difficulty', 1)
        )

        # Category could be validated before adding new question
        if not new_question.question or \
                not new_question.answer or\
                not new_question.category:
            return json.dumps({
                'success': False,
                'error': 'Missing params.'
            }), 400
        else:
            try:
                new_question.insert()
                return json.dumps(
                    {'success': True, 'question_id': new_question.id}
                ), 201
            except Exception as e:
                print(e)
                return json.dumps({
                    'success': False,
                    'error': "An error occurred"
                }), 500

    @app.route('/questions/find', methods=['POST'])
    def retrieve_questions_by_term():
        """
        Query questions searching for text fragments within question body
        ---
        tags:
          - questions
        responses:
          200:
            success: Boolean indicating operation status
            questions: Array of questions
          500:
            success: Boolean indicating operation status
            error: Unknown error
        """
        data = dict(request.form or request.json or request.data)
        search_term = data.get('searchTerm')

        if search_term:
            # `ilike` instead of `like` to be case-insensitive.
            questions = \
                Question.query.filter(Question.question.ilike(
                    f'%{search_term}%')
                ).all()

            return jsonify({
                'success': True,
                'questions': [question.format() for question in questions]
            })
        else:
            return json.dumps({
                'success': False,
                'error': 'Missing params.'
            }), 400

    @app.route('/quizzes', methods=['POST'])
    def retrieve_quiz_question():
        data = dict(request.form or request.json or request.data)
        category = data.get('quiz_category')
        previous_questions = data.get('previous_questions', [])

        if not data.get('quiz_category'):
            return json.dumps({
                'success': False,
                'error': 'Missing params.'
            }), 400
        else:
            if category['id'] == 0:
                selected_question = Question.query.filter(
                    Question.id.notin_(previous_questions)
                ).limit(1).one_or_none()
            else:
                selected_question = Question.query.filter_by(
                    category=category['id']).filter(
                    Question.id.notin_(previous_questions)
                ).limit(1).one_or_none()

            if selected_question:
                return jsonify({
                    'success': True,
                    'question': selected_question.format()
                })
            else:
                return json.dumps({
                    'success': False,
                    'error': 'Question not found.'
                }), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable entity"
        }), 422

    @app.errorhandler(500)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server error"
        }), 500

    return app
