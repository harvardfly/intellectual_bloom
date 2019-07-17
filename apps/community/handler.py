import json

import aiofiles
import os
import shortuuid
from playhouse.shortcuts import model_to_dict

from apps.community.forms import (
    CommunityGroupForm,
    GroupMemberForm,
    PostForm,
    CommentForm,
    ReplyForm
)
from apps.community.models import (
    CommunityGroup,
    CommunityGroupMember,
    CommunityPost,
    Comment,
    Reply,
    CommentLike,
    ReplyLike
)
from apps.core.utils import authenticated_async
from apps.core.utils import (
    format_arguments,
    get_int_or_none
)
from intellectual_bloom.handler import BaseHandler


class GroupsHandler(BaseHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        """
        根据group id 获取小组详情
        :param args:
        :param kwargs:
        :return:
        """
        res_data = {}
        group_id = get_int_or_none(self.get_argument("group_id", None))
        if not group_id:
            self.set_status(400)
            self.write({"content": "缺少group_id参数"})
        try:
            group_obj = await self.application.objects.get(
                CommunityGroup, id=group_id
            )
            res_data["id"] = group_id
            res_data["name"] = group_obj.name
            res_data["description"] = group_obj.description
            res_data["notice"] = group_obj.notice
            res_data["member_nums"] = group_obj.member_nums
            res_data["post_nums"] = group_obj.post_nums
            res_data["front_image"] = "{}/media/{}/".format(
                self.settings["SITE_URL"], group_obj.front_image
            )
            self.write(res_data)
        except CommunityGroup.DoesNotExist:
            self.set_status(400)
            self.write({"content": "group 不存在"})

    @authenticated_async
    async def post(self, *args, **kwargs):
        res_data = {}
        req_data = self.request.body_arguments
        req_data = format_arguments(req_data)
        group_form = CommunityGroupForm(req_data)
        if group_form.validate():
            files_meta = self.request.files.get("front_image")
            description = req_data.get("description")
            if description:
                description = description[0]
            notice = req_data.get("notice")
            if notice:
                notice = notice[0]
            new_filename = None
            if files_meta:
                # 完成图片保存并将值设置给对应的记录
                # 通过aiofiles写文件
                # 1. 文件名
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

            group_obj = await self.application.objects.create(
                CommunityGroup,
                creator=self.current_user,
                name=group_form.name.data,
                category=group_form.category.data,
                description=description,
                notice=notice,
                front_image=new_filename
            )

            res_data["id"] = group_obj.id
        else:
            self.set_status(400)
            res_data = group_form.errors
        self.finish(res_data)


class GroupListHandler(BaseHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        """
        获取小组列表、搜索
        :param args:
        :param kwargs:
        :return:
        """
        res_data = []
        community_query = CommunityGroup.extend()

        # 根据类别进行过滤
        category = self.get_argument("category", None)
        if category:
            community_query = community_query.filter(
                CommunityGroup.category == category
            )

        # 根据参数进行排序
        order = self.get_argument("o", None)
        if order:
            if order == "new":
                community_query = community_query.order_by(
                    CommunityGroup.create_time.desc()
                )
            elif order == "hot":
                community_query = community_query.order_by(
                    CommunityGroup.member_nums.desc()
                )

        per_page = self.get_argument("per_page", 10)
        page = self.get_argument("page", 1)
        per_page = get_int_or_none(per_page)
        page = get_int_or_none(page)
        if not all([page, per_page]):
            self.set_status(400)
            self.write("page 或者 per_page参数不合法")

        community_query = community_query.limit(
            per_page
        ).offset((page - 1) * per_page)
        group_objs = await self.application.objects.execute(community_query)
        for group_obj in group_objs:
            group_dict = model_to_dict(group_obj)
            group_dict["front_image"] = "{}/media/{}/".format(
                self.settings["SITE_URL"], group_dict["front_image"]
            )
            res_data.append(group_dict)

        self.finish(json.dumps(res_data))


class GroupMemberHandler(BaseHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        """
        申请加入小组
        :param args:
        :param kwargs:
        :return:
        """
        res_data = {}
        req_data = self.request.body.decode("utf8")
        req_data = json.loads(req_data)
        group_id = get_int_or_none(req_data.get("group_id"))
        group_member_form = GroupMemberForm.from_json(req_data)
        if group_member_form.validate():
            try:
                await self.application.objects.get(
                    CommunityGroup, id=group_id
                )
                await self.application.objects.get(
                    CommunityGroupMember,
                    user=self.current_user,
                    group=group_id
                )
                self.set_status(400)
                res_data["content"] = "请勿重复申请"
            except CommunityGroup.DoesNotExist:
                self.set_status(404)
            except CommunityGroupMember.DoesNotExist:
                group_member_obj = await self.application.objects.create(
                    CommunityGroupMember,
                    user=self.current_user,
                    group=group_id,
                    apply_reason=group_member_form.apply_reason.data
                )
                res_data["id"] = group_member_obj.id
                res_data["content"] = "申请成功，等待审核"
        else:
            self.set_status(400)
            res_data = group_member_form.errors

        self.finish(res_data)

    async def put(self, *args, **kwargs):
        """
        审核加入小组的申请
        :param args:
        :param kwargs:
        :return:
        """
        pass


class PostHandler(BaseHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        """
        获取小组帖子详情
        :param args:
        :param kwargs:
        :return:
        """
        res_data = {}
        group_id = get_int_or_none(self.get_argument("group_id", None))
        if not group_id:
            self.set_status(400)
            self.write({"content": "缺少group_id参数"})
        try:
            group_obj = await self.application.objects.get(
                CommunityGroup, id=group_id
            )
            await self.application.objects.get(
                CommunityGroupMember, group=group_obj,
                user=self.current_user
            )
        except Exception:
            self.set_status(400)
            self.write({"content": "group 不存在或用户尚未加入该小组"})

        post_id = get_int_or_none(self.get_argument("id", None))
        if not post_id:
            self.set_status(400)
            self.write("缺少id参数")

        try:
            post_obj = await self.application.objects.get(
                CommunityPost, id=post_id
            )
            res_data["id"] = post_id
            res_data["title"] = post_obj.title
            res_data["content"] = post_obj.content
            res_data["is_hot"] = post_obj.is_hot
            res_data["is_cream"] = post_obj.is_cream
        except CommunityPost.DoesNotExist:
            self.set_status(400)
            res_data["content"] = "帖子不存在"
        self.finish(res_data)

    @authenticated_async
    async def post(self, *args, **kwargs):
        res_data = {}
        req_data = json.loads(
            self.request.body.decode("utf8")
        )
        group_id = get_int_or_none(req_data.get("group_id"))
        group = None
        if not group_id:
            self.set_status(400)
            self.write("缺少group_id参数")
        else:
            try:
                group = await self.application.objects.get(
                    CommunityGroup, id=group_id
                )
                await self.application.objects.get(
                    CommunityGroupMember,
                    user=self.current_user,
                    status=1
                )
            except Exception:
                self.set_status(400)
                self.write("group_id不存在或该成员未加入小组")

        post_form = PostForm.from_json(req_data)
        if post_form.validate():
            post_obj = await self.application.objects.create(
                CommunityPost,
                user=self.current_user,
                title=post_form.title.data,
                content=post_form.content.data,
                group=group
            )
            res_data["id"] = post_obj.id
        else:
            res_data = post_form.errors

        self.finish(res_data)


class PostListHandler(BaseHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        """
        获取帖子列表、搜索
        :param args:
        :param kwargs:
        :return:
        """
        res_data = []
        group_id = self.get_argument("group_id", None)
        try:
            group = await self.application.objects.get(
                CommunityGroup, id=get_int_or_none(group_id)
            )
            await self.application.objects.get(
                CommunityGroupMember, user=self.current_user,
                group=group, status=1
            )
        except Exception:
            self.set_status(400)
            self.write("小组不存在或用户未成功加入小组")

        posts_query = CommunityPost.select()

        hot = self.get_argument("hot", None)
        if hot:
            posts_query = posts_query.filter(
                CommunityPost.is_hot == True
            )

        cream = self.get_argument("cream", None)
        if cream:
            posts_query = posts_query.filter(
                CommunityPost.is_cream == True
            )

        per_page = self.get_argument("per_page", 10)
        page = self.get_argument("page", 1)
        per_page = get_int_or_none(per_page)
        page = get_int_or_none(page)
        if not all([page, per_page]):
            self.set_status(400)
            self.write("page 或者 per_page参数不合法")

        posts_query = posts_query.limit(
            per_page
        ).offset((page - 1) * per_page)
        post_objs = await self.application.objects.execute(
            posts_query
        )
        for post_obj in post_objs:
            post_dict = {}
            post_dict["id"] = post_obj.id
            post_dict["user_id"] = post_obj.user_id
            post_dict["title"] = post_obj.title
            post_dict["content"] = post_obj.content

            res_data.append(post_dict)

        self.finish(json.dumps(res_data))


class CommentHandler(BaseHandler):
    @authenticated_async
    def get(self, *args, **kwargs):
        """
        获取某条评论详情
        :param args:
        :param kwargs:
        :return:
        """
        pass

    @authenticated_async
    async def post(self, *args, **kwargs):
        """
        对帖子发表评论
        :param args:
        :param kwargs:
        :return:
        """
        req_data = self.request.body.decode("utf8")
        req_data = json.loads(req_data)
        res_data = {}
        post_id = req_data.get("post_id")
        if not post_id:
            self.set_status(400)
            res_data["content"] = "缺少post_id参数"

        comment_form = CommentForm.from_json(req_data)
        if comment_form.validate():
            try:
                post_obj = await self.application.objects.get(
                    CommunityPost, id=post_id
                )
                comment_obj = await self.application.objects.create(
                    Comment, user=self.current_user,
                    post=post_obj, content=comment_form.content.data
                )
                res_data["id"] = comment_obj.id
            except CommunityPost.DoesNotExist:
                self.set_status(400)
                res_data["content"] = "帖子不存在"
        else:
            res_data = comment_form.errors
        self.finish(res_data)


class CommentListHandler(BaseHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        """
        获取帖子下的评论列表
        :param args:
        :param kwargs:
        :return:
        """
        res_data = []
        post_id = self.get_argument("post_id", None)
        per_page = self.get_argument("per_page", 10)
        page = self.get_argument("page", 1)
        per_page = get_int_or_none(per_page)
        page = get_int_or_none(page)
        if not all([page, per_page]):
            self.set_status(400)
            self.write("page 或者 per_page参数不合法")
        try:
            post_obj = await self.application.objects.get(
                CommunityPost, id=get_int_or_none(post_id)
            )
            comment_query = Comment.select().where(Comment.post == post_obj)
            comment_query = comment_query.limit(
                per_page
            ).offset((page - 1) * per_page)
            comment_objs = await self.application.objects.execute(
                comment_query
            )
            for comment_obj in comment_objs:
                comment_dict = {}
                comment_dict["id"] = comment_obj.id
                comment_dict["user_id"] = comment_obj.user_id
                comment_dict["content"] = comment_obj.content
                res_data.append(comment_dict)
        except Exception:
            self.set_status(400)
            self.write("帖子不存在")

        self.finish(json.dumps(res_data))


class ReplyHandler(BaseHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        """
        对评论回复
        :param args:
        :param kwargs:
        :return:
        """
        req_data = self.request.body.decode("utf8")
        req_data = json.loads(req_data)
        res_data = {}
        comment_id = req_data.get("comment_id")
        if not comment_id:
            self.set_status(400)
            res_data["content"] = "缺少comment_id参数"

        reply_form = ReplyForm.from_json(req_data)
        if reply_form.validate():
            try:
                comment_obj = await self.application.objects.get(
                    Comment, id=comment_id
                )
                reply_obj = await self.application.objects.create(
                    Reply, user=self.current_user,
                    comment=comment_obj,
                    content=reply_form.content.data
                )
                res_data["id"] = reply_obj.id
            except Comment.DoesNotExist:
                self.set_status(400)
                res_data["content"] = "所回复的评论不存在"

        else:
            res_data = reply_form.errors

        self.finish(res_data)


class ReplyListHandler(BaseHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        """
        获取评论下的回复列表
        :param args:
        :param kwargs:
        :return:
        """
        res_data = []
        comment_id = self.get_argument("comment_id", None)
        per_page = self.get_argument("per_page", 10)
        page = self.get_argument("page", 1)
        per_page = get_int_or_none(per_page)
        page = get_int_or_none(page)
        if not all([page, per_page]):
            self.set_status(400)
            res_data["content"] = "page 或者 per_page参数不合法"
        try:
            comment_obj = await self.application.objects.get(
                Comment, id=get_int_or_none(comment_id)
            )
            reply_query = Reply.select().where(Reply.comment == comment_obj)
            reply_query = reply_query.limit(
                per_page
            ).offset((page - 1) * per_page)
            reply_objs = await self.application.objects.execute(
                reply_query
            )
            for reply_obj in reply_objs:
                reply_dict = {}
                reply_dict["id"] = reply_obj.id
                reply_dict["user_id"] = reply_obj.user_id
                reply_dict["content"] = reply_obj.content
                res_data.append(reply_dict)
        except Exception:
            self.set_status(400)
            res_data["content"] = "评论不存在"

        self.finish(json.dumps(res_data))


class CommentLikeHandler(BaseHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        """
        评论点赞/取消赞
        :param args:
        :param kwargs:
        :return:
        """
        req_data = self.request.body.decode("utf8")
        req_data = json.loads(req_data)
        res_data = {}
        comment_id = req_data.get("comment_id")
        if not comment_id:
            self.set_status(400)
            res_data["content"] = "缺少comment_id参数"

        comment_obj = None
        try:
            comment_obj = await self.application.objects.get(
                Comment, id=comment_id
            )
        except Comment.DoesNotExist:
            self.set_status(400)
            res_data["content"] = "评论不存在"

        try:
            like_obj = await self.application.objects.get(
                CommentLike, user=self.current_user, comment=comment_obj
            )
            if like_obj.status == 1:
                like_query = CommentLike.update(status=0).where(
                    CommentLike.user == self.current_user,
                    CommentLike.comment == comment_obj
                )
                content = "取消点赞成功"
                like_status = 0
            else:
                like_query = CommentLike.update(status=1).where(
                    CommentLike.user == self.current_user,
                    CommentLike.comment == comment_obj
                )
                content = "点赞成功"
                like_status = 1

            await self.application.objects.execute(like_query)
            res_data["id"] = like_obj.id
            res_data["status"] = like_status
            res_data["content"] = content

        except CommentLike.DoesNotExist:
            comment_like_obj = await self.application.objects.create(
                CommentLike, user=self.current_user,
                comment=comment_obj,
                status=1
            )
            res_data["id"] = comment_like_obj.id
            res_data["status"] = comment_like_obj.status
            res_data["content"] = "点赞成功"

        self.finish(res_data)


class ReplyLikeHandler(BaseHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        """
        回复点赞
        :param args:
        :param kwargs:
        :return:
        """
        req_data = self.request.body.decode("utf8")
        req_data = json.loads(req_data)
        res_data = {}
        reply_id = req_data.get("reply_id")
        if not reply_id:
            self.set_status(400)
            res_data["content"] = "缺少reply_id参数"

        reply_obj = None
        try:
            reply_obj = await self.application.objects.get(
                Reply, id=reply_id
            )
        except Reply.DoesNotExist:
            self.set_status(400)
            res_data["content"] = "回复不存在"

        try:
            like_obj = await self.application.objects.get(
                ReplyLike, user=self.current_user, reply=reply_obj
            )
            if like_obj.status == 1:
                like_query = ReplyLike.update(status=0).where(
                    ReplyLike.user == self.current_user,
                    ReplyLike.reply == reply_obj
                )
                content = "取消点赞成功"
                like_status = 0
            else:
                like_query = ReplyLike.update(status=1).where(
                    ReplyLike.user == self.current_user,
                    ReplyLike.reply == reply_obj
                )
                content = "点赞成功"
                like_status = 1

            await self.application.objects.execute(like_query)
            res_data["id"] = like_obj.id
            res_data["status"] = like_status
            res_data["content"] = content

        except ReplyLike.DoesNotExist:
            reply_like_obj = await self.application.objects.create(
                ReplyLike, user=self.current_user,
                reply=reply_obj,
                status=1
            )
            res_data["id"] = reply_like_obj.id
            res_data["status"] = reply_like_obj.status
            res_data["content"] = "点赞成功"

        self.finish(res_data)
