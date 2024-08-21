using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CamMove : MonoBehaviour
{
    [Header("Movement")]
    public float moveSpeed;

    public float drag;

    public Transform orientation;

    float xInput;
    float zInput;

    Vector3 moveDirection;

    Rigidbody rb;

    private void Start()
    {
        rb = GetComponent<Rigidbody>();
        rb.freezeRotation = true; // This might not be necesary
    }

    private void FixedUpdate()
    {
        MoveCamera();
    }

    private void Update()
    {
        MyInput();
        rb.drag = drag;

    }

    private void MyInput()
    {
        xInput = Input.GetAxisRaw("Horizontal");
        zInput = Input.GetAxisRaw("Vertical");
    }

    private void MoveCamera()
    {
        // calculate movement
        moveDirection = orientation.forward * zInput + orientation.right * xInput;
        rb.AddForce(10f * moveSpeed * moveDirection.normalized, ForceMode.Force);

        if(Input.GetKey(KeyCode.LeftShift))
        {
            rb.AddForce(10f * moveSpeed * Vector3.up, ForceMode.Force);
        }

        if(Input.GetKey(KeyCode.LeftControl))
        {
            rb.AddForce(10f * moveSpeed * Vector3.down, ForceMode.Force);
        }
    }
}
