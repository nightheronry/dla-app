# pull official base image
FROM node:14-alpine AS build-step
# set working directory
WORKDIR /app

# add `/app/node_modules/.bin` to $PATH
ENV PATH /app/node_modules/.bin:$PATH

# install app dependencies
COPY package.json ./
COPY package-lock.json ./

RUN npm update
RUN npm install
# RUN npm install react-scripts@3.4.1 -g --silent

# add app
COPY . ./
RUN npm run build

FROM nginx:1.17.1-alpine
COPY nginx.conf /etc/nginx/
COPY --from=build-step /app/build /usr/share/nginx/html
EXPOSE 3000

# start app
# CMD ["npm", "start"]
