# AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements and install pre-built wheels only (no compilation needed)
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy the API code and model
COPY ./api ${LAMBDA_TASK_ROOT}/api
COPY ./model ${LAMBDA_TASK_ROOT}/model

# Set the Lambda handler
CMD ["api.lambda_handler.handler"]
