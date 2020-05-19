# -- coding: utf-8 --
from flask import Flask, jsonify, request
from flask_restplus import Api, reqparse, Resource, abort,fields
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy 
import json
from sqlalchemy import or_

app = Flask(__name__)

app.config['SECRET_KEY'] = 'adfasdg'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
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
    name_ko = db.Column(db.String(100), nullable=True)
    name_en = db.Column(db.String(100), nullable=True)
    name_ja = db.Column(db.String(100), nullable=True)
    tags = db.relationship('Tag', secondary=tags,
        backref='company')
   

class Tag(db.Model):
    __table_name__ = "tag" #table name

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(50),unique=True)
    lang = db.Column(db.String(50))  

import csv

def insert_data():    
    with open('wanted_dataset.csv', encoding='utf-8') as csvf:
        line = csv.reader(csvf, delimiter=',', quotechar='|')
        header_skip = 0

        for row in line:
            if header_skip == 0:
                header_skip = 1
            else:
                header_skip+=1
                print(row[0:2],header_skip)
                com = Company(name_ko=row[0],name_en=row[1],name_ja=row[2]) 
                db.session.add(com)
                db.session.commit()

                for tag_ko in row[3].split('|'):
                    tag = Tag.query.filter_by(tag=tag_ko).first()
                    if tag == None:
                        tag = Tag(tag=tag_ko, lang='ko')
                        db.session.add(tag)
                        db.session.commit()
                    
                    com.tags.append(tag)
                db.session.commit()
                
                for tag_en in row[4].split('|'):
                    tag = Tag.query.filter_by(tag=tag_en).first()
                    if tag==None:
                        tag = Tag(tag=tag_en, lang='en')
                        db.session.add(tag)
                        db.session.commit()
                    
                    com.tags.append(tag)
                db.session.commit()
                
                for tag_ja in row[5].split('|'):
                    tag = Tag.query.filter_by(tag=tag_ja).first()
                    if tag == None :
                        tag = Tag(tag=tag_ja, lang='ja')
                        db.session.add(tag)
                        db.session.commit()
                    
                    com.tags.append(tag)
                db.session.commit()


# @api.route('/api/company/<string:name>')
@api.doc(params={'name': 'company name(일부가능)'})
class SearchCompanyByName(Resource):
    @api.doc(params={'lang': {'description': '언어선택(ko,en,ja)중 선택가능. default:ko', 
                    'in': 'query', 'type': 'string'}})
    def get(self,name):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('lang', type=str, location='args',required=False)
            args = parser.parse_args()
        except Exception  as e :
            return {'error':str(e)}
        
        result = Company.query.filter(or_(
            Company.name_en.like('%'+name+'%'), 
            Company.name_ko.like('%'+name+'%'),
            Company.name_ja.like('%'+name+'%')
        )).all()

        response = []

        for each in result:
            response.append(check(each, args['lang']))
    
        return jsonify(response=response)

# 회사명이 비어있는 언어인경우 다른 언어의 회사명을 반환.
def check(company, lang):
    res = None
    if lang == 'ko':
        if company.name_ko !='':
            res = company.name_ko
        elif company.name_en !='':
            res = company.name_en
        elif company.name_ja !='':
            res = company.name_ja
    elif lang == 'en':
        if company.name_en !='':
            res = company.name_en
        elif company.name_ko !='':
            res = company.name_ko
        elif company.name_ja !='':
            res = company.name_ja
    else:
        if company.name_ja !='':
            res = company.name_ja
        elif company.name_ko !='':
            res = company.name_ko
        elif company.name_en !='':
            res = company.name_en
    return res

# @api.route('/api/company/search/tags/<string:tag>')
@api.doc(params={'tag': 'company tag'})
class SearchCompanyByTag(Resource):
    @api.doc(params={'lang': {'description': '언어선택(ko,en,ja)중 선택가능. default:ko', 
                    'in': 'query', 'type': 'string'}})
    def get(self, tag):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('lang', type=str, location='args',required=False)
            args = parser.parse_args()
        except Exception  as e :
            return {'error':str(e)}
        
        result = Company.query.filter(Company.tags.any(tag =tag)).all()

        response = []
        for each in result: 
            response.append(check(each, args['lang']))
            
        return jsonify(response=response)

add_tag = api.model('tag',{
    'tag':fields.String(description='회사정보에 추가하려는 tag명, 없을 경우 생성해서 추가', required=True),
    'tagLang':fields.String(description='추가되는 tag의 언어타입 설정.(ko,en,ja etc)', required=True),
})
# @api.route('/api/company/<string:name>/tags')
@api.doc(params={'name': 'company name'})
class AddTag(Resource):
    @api.doc(params={'lang': {
            'description': '언어선택(ko,en,ja)중 선택가능. default:ko', 
            'in': 'query', 'type': 'string'}
    })
    @api.expect(add_tag)
    def post(self, name):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('lang', type=str, location='args',required=False)
            args = parser.parse_args()
            body = request.json
           
            print(args,body)
        except Exception  as e :
            return {'error':str(e)}, 400
        
        
        com = Company.query.filter(
            or_(
                Company.name_en==name, 
                Company.name_ja==name, 
                Company.name_ko==name)
            ).first_or_404()

        newTag = Tag.query.filter_by(tag=body['tag']).first()
        
        if newTag == None:
            newTag = Tag(tag=body['tag'], lang=body['tagLang'])
            db.session.add(newTag)
            db.session.commit()
        
        if newTag in com.tags:
            return {'error':'exist tag'}, 400

        com.tags.append(newTag) 
        db.session.commit()             
        data = {'result':'success'}
        return jsonify(response=data)

# @api.route('/api/company/<string:name>/tags/<string:tag>')
@api.doc(params={'name': 'company name(일부가능)','tag':'제거할 company tag'})
class CompanyTagControl(Resource):
    
    def delete(self, name, tag):        
        com = Company.query.filter(
            or_(
                Company.name_en==name, 
                Company.name_ja==name, 
                Company.name_ko==name)
            ).first_or_404()
        
        tag_id =None
        for each in com.tags:
            if each.tag ==tag:
                tag_id = each
        
        if tag_id == None:
            return {"error":'Not exist tag in company info'}, 400
        com.tags.remove(tag_id)        
        db.session.commit()
        
        data = {'result':'success'}
        return jsonify(response=data)
    
api.add_resource(SearchCompanyByName, '/api/company/<string:name>')
api.add_resource(SearchCompanyByTag, '/api/company/search/tags/<string:tag>')
api.add_resource(AddTag, '/api/company/<string:name>/tags')
api.add_resource(CompanyTagControl, '/api/company/<string:name>/tags/<string:tag>')



if __name__ == '__main__':
    app.run(debug=True, port=5000)
    