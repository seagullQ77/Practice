 # -*- coding:utf-8 -*-
import json
import hashlib
from random import choice
from robot.api import logger
from warnings import catch_warnings
from JiaseLibrary.utils.lambda_db import LambdaDbCon
from JiaseLibrary.utils.http import check_json_response


class _LambdaSysUserKeywords():
    
    
    def __init__(self):      
        self._lambda_url        = None
        self._lambda_all_psd     = None
        self._lambda_super_admin = None

    def _add_user(self,account=None,real_name=None,branch_id=None):
        url = '%s/sys/users/create' %self._lambda_url
        if account is None:
            account = self._faker.phone_number()
        if real_name is None:
            real_name = self._faker.name()
        if branch_id is None:
            branch_id = self._faker.phone_number()    
        staff_id = str(self._faker.random_int(1000,9999))    
        id_card_no = self._faker.person_id()
        if int(id_card_no[16])%2 == 0:
            sex= 'F'
        else:
            sex = 'M'
        payload =   {
                    "staffId":staff_id,
                    "realName":real_name,
                    "mobilePhone":account,
                    "sex":sex,
                    "idCardNo":id_card_no,
                    "userStatus":"NORMAL",
                    "wechatId":"test",
                    "email":"test@test",
                    "userDesc":"",
                    "branchId":branch_id,
                    "account":account,
                    "id":""
                    }
        res = self._request.post(url,headers=self._headers,data=json.dumps(payload))
        status = json.loads(res.content.decode('utf-8')).get('statusCode')
        if status == '0':
            logger.info(u'新增用户成功:%s' %account)           
        else:
            logger.error(u'新增用户失败:%s' %account)
            raise AssertionError(u'新增用户失败:%s' %account)
        
        user_id = json.loads(res.content.decode('utf-8')).get('data')
        password = id_card_no[-4:] + staff_id
        return (user_id,account,password) 
    
    
    def update_user_password(self,account,old_password,new_password=None):
       
        url = '%s/sys/users/updatePassword' %self._lambda_url
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if new_password is None:
            new_password = self._lambda_all_psd
        new_password_encrpt = hashlib.sha256(new_password.encode()).hexdigest()
        old_password_encrpt = hashlib.sha256(old_password.encode()).hexdigest()
        payload =   {
                    "newPassword":new_password_encrpt,
                    "newPassword2":new_password_encrpt,
                    "oldPassword":old_password_encrpt
                    }
        
        self.login_lambda(account,old_password)  
        res = self._request.post(url,data=payload,headers=headers)
        status = json.loads(res.content.decode('utf-8')).get('statusCode')
        if status == '0':
            logger.info(u'修改账号密码成功:%s' %account)
            return json.loads(res.content.decode('utf-8')).get('data')
        else:
            logger.error(u'修改账号密码失败:%s' %account)
            raise AssertionError(u'修改账号密码失败:%s' %account)
        
    
    '''添加用户
       account:登录账号,即手机号,为None则随机生成一个手机号
       branchId:所属机构id,为None则随机选择       
    '''     
            
    def _update_user_password_by_db(self,account):
       
        lam_db = LambdaDbCon(self._lambda_host)
        lam_db.update_sys_user_password(account)
        
    
    '''添加用户
       account:登录账号,即手机号,为None则随机生成一个手机号
       branchId:所属机构id,为None则随机选择       
    '''     
            
    def add_lambda_user(self,account=None,real_name=None,branch_name=None,
                        dept_name=None,position_name=None,role_name=None):
        branch_id = self._query_branch_id(branch_name)
        user_info = self._add_user(account,real_name,branch_id)
        account = user_info[1]
        dept_id = self._query_dept_id(branch_id, dept_name)
        position_id = self._query_position_id(branch_id, position_name)
        role_id = self._query_role_id(dept_id, role_name)
    
        url = '%s/sys/users/insert_position_roles' %self._lambda_url    
        payload =   {
                    "userId":user_info[0],
                    "roleIds":role_id,
                    "positionIds":position_id,
                    "deptId":dept_id,
                    "branchId":branch_id
                    }
        res = self._request.post(url,data=payload)
        status = json.loads(res.content.decode('utf-8')).get('statusCode')
        if status == '0':
            logger.info(u'新增用户明细成功:%s' %account) 
            self._update_user_password_by_db(account)        
        else:
            logger.error(u'新增用户明细失败:%s' %account) 
            raise AssertionError(u'新增用户明细失败:%s' %account)
                    
    
    def cust_infos_queryByName(self, name):
        """
        获取客户信息
        :param name:
        :return:
        GET /cust/infos/queryByName
        """
        params = {
            "name": name,
        }
        url = '%s/cust/infos/queryByName' % self._lambda_url
        res = self._request.get(url, params=params)
        ret = check_json_response(res)
        if len(ret['data']) == 0:
            raise AssertionError("没有找到名为 %s 的管户经理 ！" % name)
        elif len(ret['data']) > 1:
            logger.warn("%s 对应不止一个管户经理，暂时只选择第一个！")
        c = ret['data'][0]
        return c

    def cust_infos_id_personal_view(self, custId, applyCode = None):
        """
        GET /cust/infos/personal/view   个人信息-详情
        :return:

        "http://lambda-web-test.ronaldinho.svc.cluster.local/cust/infos/personal/view?_ukey=5381&r=0.6827423719274031&custId=29&applyCode="
        """
        params = {
            "custId": custId,
            "applyCode":applyCode,
        }
        url = '%s/cust/infos/personal/view' % self._lambda_url
        res = self._request.get(url, params=params)
        ret = check_json_response(res)
        return ret


    def set_personal_common_info(self, id, education = None, familyAddress = None):
        """
        设置基本信息
        POST http://lambda-web-test.ronaldinho.svc.cluster.local/cust/infos/personal/update HTTP/1.1
        :return:
        """
        cust = self.cust_infos_id_personal_view(id)

        if cust['data']['education'] == '':
            education = choice(["ZJ", "ZK", "BK", "YJS", "CZ"])
        else:
            education = cust['data']['education']

        if cust['data']['familyAddress'] == '':
            familyAddress = self._faker.street_address()
        else:
            familyAddress = cust['data']['familyAddress']
        params = {
            "id": id,
            "education": education,
            "familyAddress": familyAddress,
            "custEdit": "true",
            "customerType": "NORMAL",   # 客户业务类型：NORMAL正常 , RICH富农贷客户 ,
            "creditCustType": "GR",
            "creditCustId": id,
            "creditCustName": cust['data']['baseInfo']['custName'],
            "creditIdCardNo": cust['data']['baseInfo']['idCode'],
            "creditMobilePhone": cust['data']['baseInfo']['mobilePhone'],
            "custKind": ["1", "2"],
            "idExpire": "",
            "country": "1",
            "nation": "1",
            "familyProvinceId": cust['data']['familyProvinceId'],
            "familyCityId": cust['data']['familyCityId'],
            "familyCountyId": cust['data']['familyCountyId'],
            "healthCondition": "ZC",
            "maritalCondition": "1",
            "isLimitless": "",
            "addressType": "20",
            "residenceCondition": "70",
            "residenceProvinceId": cust['data']['residenceProvinceId'],
            "residenceCityId": cust['data']['residenceCityId'],
            "residenceCountyId": cust['data']['residenceCountyId'],
            "residencePhone": "",
            "residenceAddress": cust['data']['residenceAddress'],
            "familyCount": "1",
            "familyDesc": "无",
            "workYear": "1",
            "workDesc": "无",
            "baseInfo": {
                "correlationRemark": "",                # 关联企业说明
                "custKind": "1,2",                         # 客户类型,(字典：CUST_INFO_KIND。多选项:二进制存储,1-是,0-否,顺序如下：合作商|担保客户|贷款客户,如：111表示三者都是,011表示担保客户和贷款客户,100表示合作商) ,
                "correlationRelationship": "false",   # 是否为关联关系 ,
                "mobilePhone": cust['data']['baseInfo']['mobilePhone'],
                "loginMobilePhone": cust['data']['baseInfo']['loginMobilePhone']
            }
        }
        url = '%s/cust/infos/personal/update' % self._lambda_url
        res = self._request.post(url, json = params)
        ret = check_json_response(res)


    def create_plant_business(self, custId, plantYear = 5, isMain = True):
        """
        新增种植业务
        :param plantYear:
        :return:

        POST http://lambda-web-test.ronaldinho.svc.cluster.local/cust/business/new/create HTTP/1.1
        """
        params = {
            "custId":custId,
            "businessType": "ZZ",
            "plantYear": plantYear,
            "isMain": isMain,

        }
        url = '%s/cust/business/new/create' % self._lambda_url
        res = self._request.post(url, json = params)
        ret = check_json_response(res)

    def complete_user_info(self, name):
        cust = self.cust_infos_queryByName(name)
        cust_id = cust['id']

        # 增加一个经营的业务
        self.create_plant_business(cust_id)

        # 完善基本信息
        self.set_personal_common_info(cust_id)

        aaa = 1