interface ApiResponse<T> {code: number; data: T; message?: string}

const userResp: ApiResponse<{ id: number; name: string} > = {
    code: 200,
    data : { id: 1, name: 'Alice'},
}

const countResp: ApiResponse<number> = {
    code: 200,
    data: 42,
    message: 'The answer',
}

function logResponse<T>(resp: ApiResponse<T>): void {
    console.log('code:', resp.code, 'data:', resp.data, 'message:', resp.message);
}

logResponse(userResp);
logResponse(countResp);