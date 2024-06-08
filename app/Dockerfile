# Use an official Python runtime as a parent image
FROM public.ecr.aws/lambda/python:3.10

COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the requirements file into the container at /usr/src/app
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Run app.py when the container launches
CMD ["lambda_function.handler"]