FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY . .
RUN mvn -q -DskipTests package
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /src/target/mq-producer-0.1.0.jar app.jar
ENTRYPOINT ["java","-jar","/app/app.jar"]
