# -- coding: utf-8 --
from flask import Flask, jsonify
from flask_restful import Resource, Api, abort, reqparse
from flask_sqlalchemy import SQLAlchemy#,relationship,backref
import json
from sqlalchemy import or_

app = Flask(__name__)

app.config['SECRET_KEY'] = 'adfasdg'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

api = Api(app)
db = SQLAlchemy(app)

    
tags = db.Table('tags',
    db.Column('company_id', db.Integer, db.ForeignKey('company.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
    
)


class Company(db.Model):
    __table_name__ = 'company' # table name

    id = db.Column(db.Integer, primary_key=True)
    company_name_ko = db.Column(db.String(100), nullable=True)
    company_name_en = db.Column(db.String(100), nullable=True)
    company_name_ja = db.Column(db.String(100), nullable=True)
    tags = db.relationship('Tag', secondary=tags,
        backref='company')
   

class Tag(db.Model):
    __table_name__ = "tag" #table name

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(50),unique=True)
    lang = db.Column(db.String(50))  

class SearchCompanyByName(Resource):
    def get(self,name):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('lang', type=str, location='args',required=False)
            args = parser.parse_args()
        except Exception  as e :
            return {'error':str(e)}
        
        result = Company.query.filter(or_(
            Company.company_name_en.like('%'+args['name']+'%'), 
            Company.company_name_ko.like('%'+args['name']+'%'),
            Company.company_name_ja.like('%'+args['name']+'%')
        )).all()
        data = {}
        for each in result:
            data['name'] = each[1]
            data['tags'] = each[2]

        return jsonify(response=data)
        
    def post(self):
        return {'status': 'success'}


class SearchCompanyByTag(Resource):
    def get(self, tag):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('lang', type=str, location='args',required=False)
            args = parser.parse_args()
        except Exception  as e :
            return {'error':str(e)}

        data = {}
        data2 = Company.query().filter(Company.tags.any(Tag.tag == tag))
        print(data2)
        
        query = Company.query.join(Tag, Company.id==Tag.company_id)
        if args['lang']=='en':
            result = query\
                .add_columns(Company.company_name_en,Tag.tag)\
                .filter(Tag.tag==tag)
                
        elif args['lang'] =='ja':
            result = query\
                .add_columns(Company.company_name_ja,Tag.tag)\
                .filter(Tag.tag==tag)
        else:
            result = query\
                .add_columns(Company.company_name_ko,Tag.tag)\
                .filter(Tag.tag==tag)

        # print(result)
        for each in result:
            data['name'] = each[1]
            data['tag'] = each[2]
            
        return jsonify(response=data)


class AddTag(Resource):
    def post(self, name):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('lang', type=str, location='args',required=False)
            parser.add_argument('tag', type=str, location='form',required=True)
            parser.add_argument('tagLang', type=str, location='form',required=True)
            # parser.add_argument('name', type=str, location='args',required=True)
            args = parser.parse_args()
        except Exception  as e :
            return {'error':str(e)}
        
        com = Company.query.filter(
            or_(
                Company.company_name_en==name, 
                Company.company_name_ja==name, 
                Company.company_name_ko==name)
            ).first_or_404()
        
        newTag = Tag(tag=args['tag'], lang=args['tagLang'], company_id=com.id)
        
        db.session.add(newTag)
        db.session.commit()
        
        return ''

class CompanyTagControl(Resource):
    def delete(self, name, tag):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('lang', type=str, location='args',required=False)
            parser.add_argument('tag', type=str, location='form',required=True)
            parser.add_argument('tagLang', type=str, location='form',required=True)
            # parser.add_argument('name', type=str, location='args',required=True)
            args = parser.parse_args()
        except Exception  as e :
            return {'error':str(e)}
        
        com = Company.query.filter(
            or_(
                Company.company_name_en==name, 
                Company.company_name_ja==name, 
                Company.company_name_ko==name)
            ).first_or_404()
        
        newTag = Tag(tag=args['tag'], lang=args['tagLang'], company_id=com.id)
        
        db.session.add(newTag)
        db.session.commit()
        
        return ''        
    
api.add_resource(SearchCompanyByName, '/api/company/search/name/<string:name>')
api.add_resource(SearchCompanyByTag, '/api/company/search/tags/<string:tag>')
api.add_resource(AddTag, '/api/company/<string:name>/tags')
api.add_resource(CompanyTagControl, '/api/company/<string:name>/tags/<string:tag>')

if __name__ == '__main__':
    app.run(debug=True, port=5000)