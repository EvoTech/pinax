
-- username and email can be prefixed, so, increasing length

ALTER TABLE "auth_user" ALTER "username" TYPE varchar(150);
ALTER TABLE "auth_user" ALTER "email" TYPE varchar(150);
