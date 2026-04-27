FROM node:20-alpine

ENV NEXT_PUBLIC_DJANGO_API_URL=https://django-backend-50284710838.europe-west1.run.app

WORKDIR /app
COPY . .

RUN npm install
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]