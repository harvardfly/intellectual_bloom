import json

import aiofiles
import os
import shortuuid
from playhouse.shortcuts import model_to_dict
from apps.users.models import User
from apps.question.forms import (
    QuestionForm,
    AnswerForm,
    AnswerReplyForm
)
from apps.question.models import (
    Question,
    Answer
)
from apps.core.utils import authenticated_async
from apps.core.utils import (
    get_int_or_none
)
from intellectual_bloom.handler import BaseHandler


class QuestionHandler(BaseHandler):
    async def get(self, *args, **kwargs):
        """
        获取问题列表
        :param args:
        :param kwargs:
        :return:
        """
        re_data = []
        question_query = Question.extend()

        # 根据类别进行过滤
        c = self.get_argument("c", None)
        if c:
            question_query = question_query.filter(
                Question.category == c
            )

        # 根据参数进行排序
        order = self.get_argument("o", None)
        if order:
            if order == "new":
                question_query = question_query.order_by(
                    Question.create_time.desc()
                )
            elif order == "hot":
                question_query = question_query.order_by(
                    Question.answer_nums.desc()
                )

        questions = await self.application.objects.execute(
            question_query
        )
        for question in questions:
            question_dict = model_to_dict(question)
            question_dict["image"] = "{}/media/{}/".format(
                self.settings["SITE_URL"], question_dict["image"]
            )
            re_data.append(question_dict)

        self.write(json.dumps(re_data))

    @authenticated_async
    async def post(self, *args, **kwargs):
        """
        新建问题
        :param args:
        :param kwargs:
        :return:
        """
        res_data = {}
        req_data = json.loads(
            self.request.body.decode("utf8")
        )
        question_form = QuestionForm.from_json(req_data)
        if question_form.validate():
            files_meta = self.request.files.get("image")
            new_filename = None
            if files_meta:
                for meta in files_meta:
                    filename = meta["filename"]
                    new_filename = "{uuid}_{filename}".format(
                        uuid=shortuuid.uuid(), filename=filename
                    )
                    file_path = os.path.join(
                        self.settings["MEDIA_ROOT"], new_filename
                    )
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(meta['body'])

            question_obj = await self.application.objects.create(
                Question,
                user=self.current_user,
                category=question_form.category.data,
                title=question_form.title.data,
                content=question_form.content.data,
                image=new_filename
            )

            res_data["id"] = question_obj.id
        else:
            self.set_status(400)
            res_data = question_form.errors
        self.finish(res_data)


class QuestionDetialHandler(BaseHandler):
    @authenticated_async
    async def get(self, question_id, *args, **kwargs):
        """
        根据question id 获取问题详情
        :param question_id:
        :param args:
        :param kwargs:
        :return:
        """
        question_details = await self.application.objects.execute(
            Question.extend().where(
                Question.id == get_int_or_none(question_id)
            ))

        if not question_details:
            self.set_status(404)

        item_dict = model_to_dict(question_details[0])
        item_dict["image"] = "{}/media/{}/".format(
            self.settings["SITE_URL"], item_dict["image"]
        )
        res_data = item_dict
        self.write(json.dumps(res_data))


class AnswerHanlder(BaseHandler):
    @authenticated_async
    async def get(self, question_id, *args, **kwargs):
        """
        获取某个问题的所有回答
        :param question_id:
        :param args:
        :param kwargs:
        :return:
        """
        res_data = []

        try:
            question_obj = await self.application.objects.get(
                Question, id=get_int_or_none(question_id)
            )
            answer_objs = await self.application.objects.execute(
                Answer.extend().where(
                    Answer.question == question_obj,
                    Answer.parent_answer.is_null(True)
                ).order_by(
                    Answer.create_time.desc())
            )

            for item in answer_objs:
                item_dict = {
                    "user": model_to_dict(item.user),
                    "content": item.content,
                    "reply_nums": item.reply_nums,
                    "id": item.id,
                }

                res_data.append(item_dict)
        except Question.DoesNotExist as e:
            self.set_status(404)
        self.write(json.dumps(res_data))

    @authenticated_async
    async def post(self, question_id, *args, **kwargs):
        # 新增评论
        res_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = AnswerForm.from_json(param)
        if form.validate():
            try:
                question_obj = await self.application.objects.get(
                    Question, id=get_int_or_none(question_id)
                )
                answer_obj = await self.application.objects.create(
                    Answer, user=self.current_user,
                    question=question_obj,
                    content=form.content.data
                )
                question_obj.answer_nums += 1
                await self.application.objects.update(question_obj)
                res_data["id"] = answer_obj.id
                res_data["user"] = {
                    "nick_name": self.current_user.nick_name,
                    "id": self.current_user.id
                }
            except Question.DoesNotExist as e:
                self.set_status(404)
        else:
            self.set_status(400)
            for field in form.errors:
                res_data[field] = form.errors[field][0]

        self.finish(res_data)


class AnswerReplyHandler(BaseHandler):
    @authenticated_async
    async def get(self, answer_id, *args, **kwargs):
        """
        通过回复的答案ID获取其评论信息
        :param answer_id:
        :param args:
        :param kwargs:
        :return:
        """
        res_data = []
        answer_replys = await self.application.objects.execute(
            Answer.extend().where(
                Answer.parent_answer == get_int_or_none(answer_id)
            )
        )

        for item in answer_replys:
            item_dict = {
                "user": model_to_dict(item.user),
                "content": item.content,
                "reply_nums": item.reply_nums,
                "add_time": item.add_time.strftime("%Y-%m-%d"),
                "id": item.id
            }

            res_data.append(item_dict)

        self.write(json.dumps(res_data))

    @authenticated_async
    async def post(self, answer_id, *args, **kwargs):
        """
        添加回复
        :param answer_id:
        :param args:
        :param kwargs:
        :return:
        """
        res_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = AnswerReplyForm.from_json(param)
        if form.validate():
            try:
                answer = await self.application.objects.get(
                    Answer, id=get_int_or_none(answer_id)
                )
                replyed_user = await self.application.objects.get(
                    User, id=form.replyed_user.data
                )

                reply = await self.application.objects.create(
                    Answer, user=self.current_user,
                    parent_answer=answer,
                    reply_user=replyed_user, content=form.content.data
                )

                # 修改comment的回复数
                answer.reply_nums += 1
                await self.application.objects.update(answer)

                res_data["id"] = reply.id
                res_data["user"] = {
                    "id": self.current_user.id,
                    "nick_name": self.current_user.nick_name
                }

            except Answer.DoesNotExist as e:
                self.set_status(404)
            except User.DoesNotExist as e:
                self.set_status(400)
                res_data["replyed_user"] = "用户不存在"
        else:
            self.set_status(400)
            for field in form.errors:
                res_data[field] = form.errors[field][0]

        self.write(res_data)
