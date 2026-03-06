FROM node:20-alpine

RUN apk add --no-cache openssl

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN chmod +x entrypoint.sh && npx prisma generate && npm run build

EXPOSE 3000
CMD ["./entrypoint.sh"]
